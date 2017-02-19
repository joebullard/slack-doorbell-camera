from googleapiclient import discovery, errors
from oauth2client.client import GoogleCredentials
from oauth2client.service_account import ServiceAccountCredentials
import requests

DISCOVERY_URL = 'https://{api}.googleapis.com/$discovery/rest' + \
                '?version={apiVersion}'
SCOPES = [ 'https://www.googleapis.com/auth/cloud-platform' ]

class VisionAPIClient:

    def __init__(self, json_keyfile_name=None):
        """Wrapper around a Vision API client

        Args:
            json_keyfile_name: (optional) path to service account secret JSON
                               If None, try to use application default
        Returns:
            auth'd Vision API client
        """
        if json_keyfile_name is None:
            credentials = GoogleCredentials.get_application_default()
        else:
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                    json_keyfile_name, scopes=SCOPES)

        self._client = discovery.build('vision', 'v1', credentials=credentials,
                discoveryServiceUrl=DISCOVERY_URL)

    def _build_annotation_request(self, b64image, features):
        """Build a JSON structure for a single image Vision API request.
     
        Args:
            b64image: base64-encoded image (*including file headers*)
            features: list of Vision API feature dicts
        Returns:
            dict representing a single image request
        """
        if type(features) is not list:
            features = [ features ]

        return self._client.images().annotate(body={
            'requests': [
                {
                    'image': {
                        'content': b64image
                    },
                    'features': features
                }
            ]
        })

    def annotate_image(self, b64image, features):
        """Build and execute an annotation request for a single image.

        Calling code should handle an HttpError if one is raised.

        Args:
            b64image: base64-encoded image (*including file headers*)
            features: list of Vision API feature dicts
        Returns:
            Vision API response object
        Raises:
            googleapiclient.error.HttpError (uncaught)
        """
        request = self._build_annotation_request(b64image, features)
        response = request.execute()
        return response
