from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import base64
import collections
from StringIO import StringIO
import sys
import time

import cv2
from googleapiclient import discovery, errors
from oauth2client.client import GoogleCredentials
from oauth2client.service_account import ServiceAccountCredentials
from PIL import Image
import requests

COLORS = 'danger warning good good'.split()

def log(level, message):
  """Helper logging function. Could be extended later
  """
  time_stamp = time.strftime('%Y-%m-%d %H:%M:%S')
  print('%s: (%s) %s' % (level, time_stamp, message))


def build_vision_api_client(json_keyfile_name):
  """Build the discovery client for Vision API using a Service Account
  secret key JSON file.

  TODO: Implement alternatives like default credentials, etc.

  Args:
    json_keyfile_name: path to service account secret JSON file
  Returns:
    auth'd Vision API client
  """
  url = 'https://{api}.googleapis.com/$discovery/rest?version={apiVersion}'
  scopes = [ 'https://www.googleapis.com/auth/cloud-platform' ]
  credentials = ServiceAccountCredentials.from_json_keyfile_name(
      json_keyfile_name, scopes=scopes)
  client = discovery.build('vision', 'v1', credentials=credentials,
      discoveryServiceUrl=url)
  return client

def build_vision_request(b64image, features):
  """Build a JSON structure for a single image to be added to a Vision API
  annotation request.

  Args:
    b64image: base64-encoded image (including file headers)
    features: List of Vision API feature dicts
  Returns:
    dict representing a single image request
  """
  return { 'image': { 'content': b64image }, 'features': features }

def build_face_detection_request(b64image, max_results=3):
  """Build a feature dict for face detection annotation request

  Args:
    b64image: base64-encoded image (including file headers)
    max_results: (optional) maximum number of results in response
  Returns:
    dict representing a single face detection feature request
  """
  return build_vision_request(b64image, [{
    'type': 'FACE_DETECTION',
    'maxResults': max_results
  }])

def get_face_confidences(response):
  """Extract the detection confidence for each face in the face detection
  Vision API response.

  Args:
    response: Vision API response object
  Returns:
    list of detection confidence values for each face found
  """
  confidences = []
  for resp in response['responses']:
    if 'faceAnnotations' in resp:
      for face in resp['faceAnnotations']:
        confidences.append(face['detectionConfidence'])
  return [ 0.0 ] if len(confidences) == 0 else confidences


def notify_slack(webhook_url, confidence):
  """Send message with attachment to the configured Slack Incoming Webhook.

  TODO: include the camera frame in the attachment of the message

  Args:
    webhook_url: Slack Incoming Webhook URL
    confidence: the confidence value of the prediction
  Returns:
    None
  """
  percentage = int(confidence * 100.0)
  response = requests.post(webhook_url, json={
      'attachments': [
        {
          'fallback': 'Someone is at the door!',
          'color': COLORS[percentage // 25 - 1],
          'title': '<!here>: Someone is at the door!',
          'text': "I'm %.1f%% sure" % percentage,
          'ts': time.time()
        }
      ]
    })

  if (response.status_code == 200):
    log('INFO', 'Successfully posted message to Slack')
  else:
    log('ERROR', 'Failed to send Slack message: ' + response.text)


def detect_faces(vision_api_client, camera, webhook_url, sleep_secs,
    timeout_secs, window_size, min_confidence, resize=None, verbose=False):
  """Keep reading frames from the camera and checking them for presence of
  any faces. When a face is present, notify your configured Slack Incoming
  Webhook that someone is at the door.

  We are sampling frames quite often, but we wouldn't want to send a message
  to Slack for each frame, so there detection of a face causes us to enter
  a sub-loop which waits for the faces to disappear.

  The confidence is averaged over a specified number of camera frames /
  requests. If one frame contains multiple faces, the confidence values
  are treated as if they were found in invidual frames.

  e.g. if `window_size=10` and there are 2 faces in each frame (assuming they
  all pass the `min_confidence`), then it would only require 5 frames to
  trigger the Slack notification.

  Args:
    vision_api_client: Google Cloud Vision API client object
    camera: CV2 VideoCapture object
    webhook_url: Slack Incoming Webhook URL
    sleep_secs: number of seconds to sleep between frames
    window_size: number of frames over which to average confidence
    min_confidence: minimum threshold for detection confidence
    resize: (optional) tuple of (width, height) for resizing camera frames
  Returns:
    None
  """
  frame_size= (int(camera.get(3)), int(camera.get(4)))
  window = collections.deque([0]*window_size, maxlen=window_size)
  triggered = False
  notified = False
  prev_trigger = False
  secs_since_notification = timeout_secs

  while True:
    grabbed, frame = camera.read()
    if not grabbed:
      log('WARNING', 'Could not read frame from camera. Aborting detection')
      break

    # Convert to RGB (cv2 uses BGR by default)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Wrap JPEG headers around the frame(required by Vision API)
    buff = StringIO()
    img = Image.frombytes('RGB', frame_size, frame.tobytes())
    if resize is not None:
      img = img.resize(resize)
    img.save(buff, format='jpeg')

    # Create a Vision API request
    b64image = base64.b64encode(buff.getvalue()).decode('UTF-8') 
    request  = vision_api_client.images().annotate(body={
        'requests': build_face_detection_request(b64image)
      })

    try:
      response = request.execute()
    except errors.HttpError as err:
      log('ERROR', 'Vision API request failed: ' + err)
      continue
      
    if verbose:
      log('INFO', 'Vision API request successful')

    # Update window and determine if we should notify Slack
    window.extend(get_face_confidences(response))
    confidence = sum(window) / window_size
    triggered  = confidence >= min_confidence

    if verbose:
      log('INFO', 'Confidence of face presence: %f' % confidence)

    if triggered:
      if not notified and secs_since_notification >= timeout_secs:
        notify_slack(webhook_url, confidence)
        notified = True
        secs_since_notification = 0
    else:
      notified = False
      secs_since_notification += sleep_secs

    time.sleep(sleep_secs)


def main(argv):
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--json-keyfile',
      required=True,
      type=str,
      help='Path to a Google Cloud service account credentials JSON'
    )
  parser.add_argument(
      '--webhook-url',
      required=True,
      type=str,
      help='Slack Incoming Webhook URL'
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
      help='Camera frame width'
    )
  parser.add_argument(
      '--height',
      required=False,
      default=320,
      type=int,
      help='Camera frame height'
    )
  parser.add_argument(
      '--detection-sleep-secs',
      required=False,
      default=1.0,
      type=float,
      help='Number of seconds to sleep between reading camera frames'
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
      help='If True, print update of every single camera polling iteration'
    )
  args = parser.parse_args(argv)

  # We need a working camera (VideoCapture) and an auth'd API client
  camera = cv2.VideoCapture(args.device_index)
  client = build_vision_api_client(args.json_keyfile)

  # Run the detection loop (program will exit only if it loses camera feed)
  # See docstring for `detect_faces()`
  detect_faces(client, camera,
      args.webhook_url,
      args.detection_sleep_secs,
      args.detection_timeout_secs,
      args.detection_window_size,
      args.detection_min_confidence,
      resize=(args.width, args.height),
      verbose=args.verbose
    )

if __name__ == '__main__':
  main(sys.argv[1:])
