import argparse
import sys
import time

from doorbell import SlackDoorbell
from ringer import FaceDetectionDoorbellRinger
from visionapi import VisionAPIClient

def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--motion-output-dir',
        required=True,
        type=str,
        help='Path to the motion daemon output directory'
    )
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
        '--sleep-secs',
        required=False,
        default=1.0,
        type=float,
        help='Number of seconds to sleep between image polling'
    )
    parser.add_argument(
        '--min-confidence',
        required=False,
        default=0.70,
        type=float,
        help='Minimum detection confidence threshold of face detection'
    )
    parser.add_argument(
        '--timeout-secs',
        required=False,
        default=10,
        type=float,
        help='Number of seconds to wait before ringing again')
    parser.add_argument(
        '--verbose',
        required=False,
        action='store_true',
        help='If True, print update of every single detection iteration'
    )
    return parser.parse_args(argv)

def main(argv):
    args = parse_args(argv)
    vision = VisionAPIClient(args.json_keyfile)
    doorbell = SlackDoorbell(args.webhook_url)
    ringer = FaceDetectionDoorbellRinger(vision, doorbell,
        args.min_confidence, args.timeout_secs, verbose=args.verbose)
    ringer.run(args.motion_output_dir, args.sleep_secs)

if __name__ == '__main__':
    main(sys.argv[1:])
