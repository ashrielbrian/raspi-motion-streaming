import io
import datetime
import imutils
import json
import cv2
from PIL import Image
import logging
import numpy as np

with open("conf.json", "r") as f:
    conf = json.load(f)


avg = None
last_uploaded = datetime.datetime.now()
motion_counter = 0
MOTION_TEXT = "Motion detected"


def get_motion_frame(frame_bytes: bytes):
    print(f"Geting motion frame of byte length: {len(frame_bytes)}")
    global avg, motion_counter, last_uploaded

    if len(frame_bytes) == 0:
        return bytes("", "utf-8")
    # load as PIL image from bytes
    image = Image.open(io.BytesIO(frame_bytes))
    frame = np.asarray(image)
    print(f"Frame loaded with size: {frame.shape}..")

    timestamp = datetime.datetime.now()
    text = "None"

    # resize frame, convert to grayscale and blur
    frame = imutils.resize(frame, width=500)
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    print(f"Successfully resized, grayscaled, blurred. New size: {gray.shape}")

    # if the average frame is None, initialize it
    if avg is None:
        print("[INFO]: starting background model...")
        avg = gray.copy().astype(float)

    # accumulate the weighted average between the current frame and
    # previous frames, then compute the difference between the current
    # frame and running average
    cv2.accumulateWeighted(gray, avg, 0.5)
    frame_delta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

    thresh = cv2.threshold(frame_delta, conf["delta_thresh"], 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)

    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    for c in cnts:
        # if contours is too small, ignore
        if cv2.contourArea(c) < conf["min_area"]:
            continue

        # compute the bounding box for the contour, draw it on the frame, and update the text
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        text = MOTION_TEXT

    # draw the text and timestamp on the frame
    ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
    cv2.putText(
        frame,
        f"Status: {text}",
        (10, 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 0, 255),
        2,
    )
    cv2.putText(
        frame,
        ts,
        (10, frame.shape[0] - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.35,
        (0, 0, 255),
        1,
    )
    frame = imutils.resize(frame, width=640)
    print(f"New size of frame before saving: {frame.shape}")
    frame = Image.fromarray(frame)
    if text == MOTION_TEXT:
        # check to see if enough time has passed between saves
        if (timestamp - last_uploaded).seconds >= conf["min_upload_seconds"]:
            motion_counter += 1

            # check to see if num of frames with consistent motion is high enough
            # then save to file
            if motion_counter >= conf["min_motion_frames"]:
                frame.save(f"data/{ts}.jpeg")

                # update the last uploaded timestamp and reset motion counter
                motion_counter = 0
                last_uploaded = timestamp
    else:
        motion_counter = 0

    buf = io.BytesIO()
    frame.save(buf, "JPEG")
    buf.seek(0)
    return buf.getvalue()
