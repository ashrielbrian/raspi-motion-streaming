# Intro

Web streaming & still image motion detection capture on the Raspberry Pi.

This project:
- streams the output of the picamera through a HTTP server
- detects motion using a simple rules-based algorithm (see below)
- captures still images and saves to a `data/` directory in the project directory

Motion detection algorithm taken from [pyimagesearch](https://pyimagesearch.com/2015/06/01/home-surveillance-and-motion-detection-with-the-raspberry-pi-python-and-opencv/), with the streaming component adapted from  [picamera's advanced recipes](https://picamera.readthedocs.io/en/latest/recipes2.html).

# Usage
```
    python3 -m venv .venv
    source .venv/bin/activate

    pip install -r requirements.txt -i https://www.piwheels.org/simple
    python main.py
```

where the `-i` flag is used to find pre-compiled wheels at the piwheels index (way faster installation on raspberry pi).

Then, open your favourite browser, and provided your Pi is on the same local network, go to `http://<raspberry-pi-local-ip>:8000/`. Say hi to the camera!

If you want your stream accessible on the public internet (hello justin.tv), download [ngrok](https://ngrok.com/):

```
    ngrok http -region=ap -auth="<user>:<pw>" 8000
```

# Notes

Tested on a raspberry pi 4B, with 4GB RAM, and a v2.1 camera module.

# Future work

- Instead of capturing and saving still images, capture the past x seconds of video.