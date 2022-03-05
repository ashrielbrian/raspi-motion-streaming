# Web streaming example
# Source code from the official PiCamera package
# http://picamera.readthedocs.io/en/latest/recipes2.html#web-streaming
import json
import io
from typing import Optional
import picamera
import logging
import socketserver
from threading import Condition
from http import server
import motion_detector as motion

PAGE = """\
<html>
    <head>
        <title>Motion detection streaming</title>
    </head>
    <body>
        <center><h1>Motion detection streaming</h1></center>
        <center><img src="stream.mjpg" width="640" height="480"></center>
    </body>
</html>
"""


class MotionFrameException(Exception):
    pass


class StreamingOutput(object):
    def __init__(self):
        self.frame: Optional[bytes] = None
        self.buffer = io.BytesIO()
        self.condition = Condition()
        self.error = (False, None)

    def write(self, buf):
        if buf.startswith(b"\xff\xd8"):

            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            try:
                full_frame = self.buffer.getvalue()
                self.frame = motion.get_motion_frame(full_frame)
            except Exception as e:
                print(e)
                self.error = (True, e)
                raise MotionFrameException(output.error[1])

            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)

        return self.buffer.write(buf)


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(301)
            self.send_header("Location", "/index.html")
            self.end_headers()
        elif self.path == "/index.html":
            content = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", f"{len(content)}")
            self.end_headers()
            self.wfile.write(content)
        elif self.path == "/stream.mjpg":
            self.send_response(200)
            self.send_header("Age", "0")
            self.send_header("Cache-Control", "no-cache, private")
            self.send_header("Pragma", "no-cache")
            self.send_header(
                "Content-Type", "multipart/x-mixed-replace; boundary=FRAME"
            )
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b"--FRAME\r\n")
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", f"{len(frame)}")
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
            except Exception as e:
                logging.warning(
                    "Removed streaming client %s: %s", self.client_address, str(e)
                )
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    with open("conf.json", "r") as f:
        conf = json.load(f)

    res = f"{conf['resolution'][0]}x{conf['resolution'][1]}"
    with picamera.PiCamera(resolution=res, framerate=conf["fps"]) as camera:
        output = StreamingOutput()
        # Uncomment the next line to change your Pi's Camera rotation (in degrees)
        # camera.rotation = 90
        try:
            camera.start_recording(output, format="mjpeg")
            address = ("", 8000)
            server = StreamingServer(address, StreamingHandler)
            server.serve_forever()
        finally:
            camera.stop_recording()
