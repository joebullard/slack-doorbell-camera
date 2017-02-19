import argparse
import collections
import sys
import time

import cv2
import googleapiclient.errors

from face_detector import FaceDetector, VideoCaptureError
from doorbell import SlackDoorbell, SlackDoorbellError
from visionapi import VisionAPIClient
import logger

def run_detection(detector, doorbell, sleep_secs, timeout_secs, window_size,
        min_confidence, verbose=False):
    """Keep checking the video capture and ring the doorbell when we are
    confident that faces are present.

    1. Check the current video frame for presence of faces
    2. Maintain a fixed-length (`window_size`) deque of the confidence values
       of each face found (i.e. if 3 faces are found in one frame, then all 3
       are appended to the deque). If no faces were found, then a single `0` is
       appended to the deque.
    3. If the average confidence exceeds the `min_confidence` and if we have
       not already rung the doorbell (based on `timeout_secs`), then ring it.
    4. Repeat until we cannot read new frames or program is terminated

    Args:
        detector: FaceDetector object
        doorbell: SlackDoorbell object
        sleep_secs: number of seconds to sleep between frames
        window_size: number of frames over which to average confidence
        timeout_secs: number of seconds to wait before ringing again (see above)
        min_confidence: minimum threshold for detection confidence
        verbose: (optional) if True, log info in every loop iteration, else
                 only log important messages
    Returns:
        None
    """
    window = collections.deque([0]*window_size, maxlen=window_size)
    rang = False
    secs_since_rang = timeout_secs

    while True:
        # 1. Get confidence of faces currently in view
        try:
            face_confidences = detector.detect_faces()
        except VideoCaptureError as err:
            logger.fatal(err)
            break
        except googleapiclient.errors.HttpError as err:
            logger.error(err)
            continue

        # 2. Average the confidence values of all faces within window
        window.extend(face_confidences)
        confidence = sum(window) / window_size

        if verbose:
            logger.info('Confidence of face presence: %f' % confidence)

        # 3. Determine if we should ring the doorbell
        if confidence >= min_confidence:
            if not rang and secs_since_rang >= timeout_secs:
                try:
                    doorbell.ring(confidence=confidence)
                except SlackDoorbellError as err:
                    # TODO: Not all failed rings should be fatal
                    logger.fatal(err)
                    break

                rang = True
                secs_since_rang = 0
            elif verbose:
                logger.info('Faces detected, but already rang doorbell')
        else:
            rang = False
            secs_since_rang += sleep_secs
        time.sleep(sleep_secs)

def main(argv):
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--webhook-url',
      required=True,
      type=str,
      help='Slack Incoming Webhook URL'
    )
  parser.add_argument(
      '--json-keyfile',
      required=False,
      default=None,
      type=str,
      help='Path to a Google Cloud service account credentials JSON'
    )
  parser.add_argument(
      '--device-index',
      required=False,
      default=0,
      type=int,
      help='Camera device index (typically 0)'
    )
  parser.add_argument(
      '--width',
      required=False,
      default=480,
      type=int,
      help='Video frame width'
    )
  parser.add_argument(
      '--height',
      required=False,
      default=320,
      type=int,
      help='Video frame height'
    )
  parser.add_argument(
      '--detection-sleep-secs',
      required=False,
      default=1.0,
      type=float,
      help='Number of seconds to sleep between reading frames from video'
    )
  parser.add_argument(
      '--detection-timeout-secs',
      required=False,
      default=10,
      type=float,
      help='Number of seconds after a notification during which no new notifications should be sent.'
    )
  parser.add_argument(
      '--detection-window-size',
      required=False,
      default=4,
      type=int,
      help='Number of frames to consider when detecting faces'
    )
  parser.add_argument(
      '--detection-min-confidence',
      required=False,
      default=0.70,
      type=float,
      help='Minimum detection confidence threshold (averaged over window)'
    )
  parser.add_argument(
      '--verbose',
      required=False,
      action='store_true',
      help='If True, print update of every single detection iteration'
    )

  args = parser.parse_args(argv)

  doorbell = SlackDoorbell(args.webhook_url)
  camera = cv2.VideoCapture(args.device_index)
  vision = VisionAPIClient(args.json_keyfile)
  detector = FaceDetector(camera, vision,
                resize_resolution=(args.width, args.height))

  # The detection loop will exit only if it loses camera feed
  # See docstring for `run_detection()`
  run_detection(detector, doorbell,
      args.detection_sleep_secs,
      args.detection_timeout_secs,
      args.detection_window_size,
      args.detection_min_confidence,
      verbose=args.verbose
    )

if __name__ == '__main__':
  main(sys.argv[1:])
