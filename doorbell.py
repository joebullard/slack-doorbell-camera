import requests

COLORS = 'danger warning good good'.split()

class SlackDoorbellError(Exception):

    def __init__(self, message, http_status_code):
        super(Exception, self).__init__('(%d) "%s"' % (message, http_code))
        self.http_status_code = http_status_code

class SlackDoorbell:

    DEFAULT_MESSAGE = '<!here>: Someone is at the door!'

    def __init__(self, webhook_url):
        """Doorbell which 'rings' a Slack channel through an Incoming Webhook

        Args:
            webhook_url: valid Slack Incoming Webhook URL
        Returns:
            None
        """
        self._webhook_url = webhook_url

    def ring(self, message=DEFAULT_MESSAGE, confidence=None):
        """Ring the doorbell (i.e. send message to the Incoming Webhook.)

        Args:
            message: (optional) non-standard message text
            confidence: (optional) confidence value of the doorbell trigger
        Returns:
            None
        Raises:
            SlackDoorbellError (based on bad HTTP status codes)
        """
        body = { 'attachments': [ { 'fallback': message, 'title': message } ] }

        # Optional confidence formatting
        if confidence is not None:
            percentage = int(confidence * 100.0)
            body['attachments'][0]['text'] = "I'm %.1f%% sure" % percentage
            body['attachments'][0]['color'] = COLORS[percentage // 25 - 1]
        else:
            body['attachments'][0]['color'] = 'warning'

        response = requests.post(self._webhook_url, json=body)

        if (response.status_code != 200):
            raise SlackDoorbellError(response.content, response.status_code)
