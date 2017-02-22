import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from detector import FaceDetector
from doorbell import SlackDoorbellError
from visionapi import VisionAPIError
from logger import Logger, LogLevel

ALLOWED_EXTENSIONS = 'jpg jpeg png gif'.split()

class FaceDetectionDoorbellRinger(FileSystemEventHandler):

    def __init__(self, vision_api_client, doorbell, min_confidence,
        timeout_secs, verbose=False):
        """This is a `watchdog` event handler which monitors a directory for
        newly created image files, checking them for the presence of faces, and
        ringing a doorbell if it believes strongly enough that someone is
        waiting.

        All Vision API face detection annotations will have an associated
        confidence value, which must exceed the specified minimum confidence
        threshold (`min_confidence`) in order to trigger a doorbell ring.

        We also do not want to repeatedly ring for the same group of visitors,
        so we do not even bother checking for faces if we are within the
        specified `timeout_secs`.

        The `Observer` object for this event handler is created inside of here
        for simplicity's sake.

        Only the `on_create()` method will be overridden here, as we do not
        care about other file-system events.

        Args:
            vision_api_client: `visionapi.VisionAPIClient` object
            doorbell: `doorbell.SlackDoorbell` object
            min_confidence: minimum confidence threshold for face detection
            timout_secs: number of seconds to wait before ringing again
            verbose: (optional) if True, print info message for every event
        Returns:
            `FaceDetectionDoorbellRinger` event handler
        """
        self._detector = FaceDetector(vision_api_client)
        self._doorbell = doorbell
        self._min_confidence = min_confidence
        self._timeout_secs = timeout_secs
        self._time_of_prev_ring = 0
        self._logger = Logger(LogLevel.ANY if verbose else LogLevel.INFO)

    def _file_is_allowed(self, event):
        return not event.is_directory and \
            event.src_path.split('.')[-1].lower() in ALLOWED_EXTENSIONS

    def _already_rang_doorbell(self):
        return int(time.time()) - self._time_of_prev_ring < self._timeout_secs

    def _get_confidence(self, image_path):
        try:
            faces = self._detector.detect_faces(image_path)
            confidence = sum(faces) / len(faces)
        except VisionAPIError as err:
            self._logger.warning(err, 'Treating this as 0% confidence')
            confidence = 0. 
        return confidence

    def _ring_doorbell(self, confidence):
        try:
            self._doorbell.ring(confidence=confidence)
            self._time_of_prev_ring = int(time.time())
        except SlackDoorbellError as err:
            # TODO: Not all failed rings should be critical
            self._logger.critical(err)
            self._observer.stop()

    def on_created(self, event):
        """Overrides the `watchdog.events.FileSystemEventHandler.on_created()`.
        
        When a new file is created in our watch directory:
            1. Check if this was an image file
            2. Check if we have already rang the doorbell recently
            3. Check if faces are present in the image
            4. Check if average confidence of faces exceeds threshold
            5. Ring doorbell
            6. Update the timeout clock

        Args:
            event: `watchdog.events.FileSystemEvent` object
        Returns:
            None
        """
        self._logger.debug('Event triggered')

        if self._file_is_allowed(event) and not self._already_rang_doorbell():
            self._logger.debug('Checking for faces')
            confidence = self._get_confidence(event.src_path)
            self._logger.debug('Confidence of faces: %f' % confidence)

            if confidence >= self._min_confidence:
                self._logger.info('Ringing doorbell')
                self._ring_doorbell(confidence)
            else:
                self._logger.debug('Did not ring doorbell')
        else:
            self._logger.debug('Ignored event')

    def run(self, motion_output_dir, sleep_secs, recursive=False):
        """Create and run a `watchdog.observers.Observer` over the `motion`
        process's output directory, triggering potential doorbell rings (see
        `on_created()` meothod of this class).

        Args:
            motion_output_dir: path to `motion` daemon image output directory
            sleep_secs: number of seconds to sleep between polling
            recursive: (optional) recursively watch directory
        Returns:
            None
        """
        observer = Observer()
        observer.schedule(self, motion_output_dir, recursive=recursive)
        observer.start()

        self._logger.info('Monitoring %s for images %srecursively' % (
            motion_output_dir, '' if recursive else 'non-'))

        try:
            while True:
                time.sleep(sleep_secs)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
