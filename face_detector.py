import base64
from StringIO import StringIO

import cv2
from PIL import Image

class VideoCaptureError(Exception):

    def __init__(self, message):
        super(Exception, self).__init__(message)

class FaceDetector:

    def __init__(self, video_capture, vision_api_client,
            resize_resolution=None):
        """Face detection around a OpenCV VideoCapture device using the Google
        Vision API.

        Args:
            video_capture: cv2.VideoCapture object
            vision_api_client: VisionAPIClient object
            resize_resolution: (optional) tuple of (width, height) for resizing
                               images sent to Vision API
        Returns:
            None
        """
        self._capture = video_capture
        self._vision = vision_api_client
        self._resize = resize_resolution
        self.resolution = (int(self._capture.get(3)),
                           int(self._capture.get(4)))

    def _get_frame(self):
        """Attempt to read one frame from the capture device.

        Returns:
            3D array representing the RGB content of the current frame
        Raises:
            VideoCaptureError
        """
        grabbed, frame = self._capture.read()
        if not grabbed:
            raise VideoCaptureReadError('Failed to read frame!')
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame

    def _resize_and_encode(self, frame):
        """Wrap JPEG headers around the frame (necessary for Vision API),
        resize if desired, and encode as a base-64 string in UTF-8 (also
        required by Vision API).

        Use a StringIO buffer to avoid having to save the file to disk.

        Args:
            frame: image array (presumably returned by `_get_frame()`
        Returns:
            base64 string of input image
        """
        frame = self._get_frame()
        buff  = StringIO()
        image = Image.frombytes('RGB', self.resolution, frame.tobytes())

        if self._resize is not None:
            image = image.resize(self._resize)
        image.save(buff, format='jpeg')

        return base64.b64encode(buff.getvalue()).decode('UTF-8') 

    def _extract_face_confidences(self, annotation_response):
        """Extract the detection confidence for each face in a Vision API
        annotation response.

        Args:
          annotation_response: Vision API response object
        Returns:
          list of detection confidence values for each face found,
          or `[ 0.0 ]` if no faces were found.
        """
        confidences = []
        for resp in annotation_response['responses']:
            if 'faceAnnotations' in resp:
                for face in resp['faceAnnotations']:
                    confidences.append(face['detectionConfidence'])
        return [ 0.0 ] if len(confidences) == 0 else confidences

    def detect_faces(self):
        """Take a picture and determine presence of any faces.

        Returns:
            list of floats representing the confidence values for each face
            detected in the current frame
        Raises:
            VideoCaptureError (uncaught)
            googleapiclient.errors.HttpError (uncaught)
        """
        frame = self._get_frame()
        b64image = self._resize_and_encode(frame)
        response = self._vision.annotate_image(b64image, {
            'type': 'FACE_DETECTION',
        })
        return self._extract_face_confidences(response)
