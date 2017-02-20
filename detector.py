import base64

class FaceDetector():

    def __init__(self, vision_api_client):
        """Detects confidence of the presence of faces in an image using the
        Google Vision API.

        Args:
            vision_api_client: VisionAPIClient object
        Returns:
            `FaceDetector` object
        """
        self._vision_api_client = vision_api_client

    def _read_and_encode_image(self, image_path):
        """Read and encode an image as a base-64 string in UTF8, including file
        headers, as required by the Vision API.

        Args:
            path: string path of image
        Returns:
            base64 string representing image (including file headers)
        """
        data = open(image_path, 'rb').read()
        return base64.b64encode(data).decode('UTF-8') 

    def _extract_face_confidence_values(self, annotation_response):
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

    def detect_faces(self, image_path):
        """Detect presence of faces in a given image using Vision API.

        Args:
            image_path
        Returns:
            list of floats representing the confidence values for each face
            detected in the current frame
        Raises:
            VisionAPIError (uncaught)
        """
        b64image = self._read_and_encode_image(image_path)
        response = self._vision_api_client.annotate_image(b64image, {
            'type': 'FACE_DETECTION',
        })
        return self._extract_face_confidence_values(response)
