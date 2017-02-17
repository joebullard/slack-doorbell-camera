# slack-doorbell-camera

Small office doorbell system using Slack Incoming Webhooks.

## Install requirements

Use of the webcam depends on OpenCV (python package `cv2`), which is not easy
to install in a virtualenv, so please install it correctly for python on your
system, and create your virtualenv with default to system site packages:

```
virtualenv --system-site-packages venv
source venv/bin/activate
pip install -I -r requirements.txt
```

The `-I` for pip is required to ignore the system packages that may be in
`requirements.txt`.

## Setup Environment

#### Create a Slack Incoming Webhook

Follow the guide on
[Creating Incoming Webhooks](https://api.slack.com/incoming-webhooks)
for your Slack team.

Customize it how you like. But you need to use the URL you are given on that
page.

Would be nice if this repo was transformed into a bot, so the team owner
doesn't have to configure it themselves, but I don't feel like hosting this or
submitting it to the app registry, etc. (maybe someday).

#### Enable Cloud Vision API

Currently this is only coded to use a Service Account credentials file
(supplied by you). Follow the guide on
[Service Accounts](https://cloud.google.com/compute/docs/access/service-accounts),
and make sure to enable Cloud Vision API in your project.

## Run the "bot"

Not an actual Slack Bot, but you can host this wherever you want and have it
read from your camera.

`python doorbell.py --json-keyfile /path/to/service-account-credentials.json`

For full list of arguments, run `python doorbell.py -h`
