# slack-doorbell-camera

Small office doorbell system using a 
[Slack Incoming Webhooks](https://api.slack.com/incoming-webhooks),
triggered by motion detection using 
[Motion](http://lavrsen.dk/foswiki/bin/view/Motion/WebHome),
and evaluated by
[Google Cloud Vision API](https://cloud.google.com/vision/).

## Hardware Setup

I am using a Raspberry Pi with a cheap USB webcam, but any system with any
attached camera should be fine.

*TODO:* add pictures

## Software and Dependencies 

### [Motion](http://lavrsen.dk/foswiki/bin/view/Motion/WebHome)

The current setup depends on
[Motion](http://lavrsen.dk/foswiki/bin/view/Motion/WebHome),
a popular program for motion detection in webcams (also does streaming).

To install Motion in Ubuntu (or Raspbian):
```
sudo apt-get install motion
```

Follow the
[Motion configuration guide](
http://www.lavrsen.dk/foswiki/bin/view/Motion/ConfigFileOptions),
or modify `motion.conf.example` in this repo (which has been stripped down to bare minimum settings for clarity).

Run motion with your edited config file:
```
motion -c ./motion.conf.example
```

### Create a Slack Incoming Webhook

Follow the guide on
[Creating Incoming Webhooks](https://api.slack.com/incoming-webhooks)
for your Slack team.

Customize it how you like. But you need to use the URL you are given on that
page.

Would be nice if this repo was transformed into a bot, so the team owner
doesn't have to configure it themselves, but I don't feel like hosting this or
submitting it to the app registry, etc. (maybe someday).

### Enable Cloud Vision API

Currently this only supports the use of a Service Account credentials file, or if none is provided, your gcloud default credentials.

Follow the guide on
[Service Accounts](https://cloud.google.com/compute/docs/access/service-accounts),
and make sure to enable Cloud Vision API in your project.

### Python dependencies

Use a virtualenv as usual:
```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the "bot"

Not an actual Slack Bot, but you can host this wherever you want and have it
read from your camera.

```
python main.py \
    --motion-output-dir /mycam \
    --stream-addr myExternalIP:8081 \
    --json-keyfile /path/to/service-account-credentials.json \
    --webhook-url https://hooks.slack.com/services/my/webhook/url
```

For full list of arguments, run `python main.py -h`
