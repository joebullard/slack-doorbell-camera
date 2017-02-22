import requests

COLORS = 'danger warning good good'.split()

class SlackDoorbellError(Exception):

    def __init__(self, message, http_code):
        super(Exception, self).__init__('(%d) "%s"' % (message, http_code))
        self.http_code = http_code

class SlackDoorbell:

    DEFAULT_MENTION = '<!here>:'
    DEFAULT_MESSAGE = 'Someone is at the door!'

    def __init__(self, webhook_url, stream_addr=None):
        """Doorbell which 'rings' a Slack channel through an Incoming Webhook

        Args:
            webhook_url: valid Slack Incoming Webhook URL
            stream_addr: (optional) address of motion cam stream
        Returns:
            SlackDoorbell object
        """
        self._webhook_url = webhook_url
        self._stream_addr = stream_addr

    def ring(self, message=DEFAULT_MESSAGE, mention=DEFAULT_MENTION,
            confidence=None):
        """Ring the doorbell (i.e. send message to the Incoming Webhook.)

        Args:
            message: (optional) for non-standard message text
            mention: (optional) for non-standard @mention
            confidence: (optional) confidence value of the doorbell trigger
        Returns:
            None
        Raises:
            SlackDoorbellError (based on bad HTTP status codes)
        """
        attachment = {
                'fallback': message,
                'pretext': mention,
                'title': message,
                'color': 'warning',
            }

        # Include link to live stream (if there is one)
        if self._stream_addr is not None:
            attachment['text'] = '<%s|Live stream>' % self._stream_addr

        # Optional confidence formatting
        if confidence is not None:
            percentage = int(confidence * 100.0)
            attachment['footer'] = "I'm %.1f%% sure" % percentage
            attachment['color'] = COLORS[percentage // 25 - 1]

        response = requests.post(self._webhook_url,
                json={ 'attachments': [ attachment ] })

        if (response.status_code != 200):
            raise SlackDoorbellError(response.content, response.status_code)
