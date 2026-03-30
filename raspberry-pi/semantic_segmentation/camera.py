import time
from threading import Thread

import cv2


class PiCameraStream:
    def __init__(self, width=320, height=240, brightness=None, hflip=False, vflip=False):
        from picamera2 import Picamera2

        self.picam = Picamera2()

        full_fov_mode = None
        for mode in self.picam.sensor_modes:
            if mode["crop_limits"][0] == 0 and mode["crop_limits"][1] == 0:
                full_fov_mode = mode
                break

        config = self.picam.create_video_configuration(
            main={"size": (width, height), "format": "RGB888"},
            sensor={
                "output_size": full_fov_mode["size"],
                "bit_depth": full_fov_mode["bit_depth"],
            },
        )

        if hflip or vflip:
            from libcamera import Transform
            config["transform"] = Transform(hflip=int(hflip), vflip=int(vflip))

        self.picam.configure(config)

        if brightness is not None:
            self.picam.set_controls({"Brightness": float(brightness)})

        self.picam.start()
        time.sleep(1)
        self.frame = self.picam.capture_array()
        self.running = True
        Thread(target=self._update, daemon=True).start()

    def _update(self):
        while self.running:
            self.frame = self.picam.capture_array()

    def read(self):
        return self.frame is not None, self.frame

    def stop(self):
        self.running = False
        self.picam.stop()

    def isOpened(self):
        return self.running


class USBCameraStream:
    def __init__(self, src=0, width=640, height=480):
        self.cap = cv2.VideoCapture(src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.ret, self.frame = self.cap.read()
        self.running = True
        Thread(target=self._update, daemon=True).start()

    def _update(self):
        while self.running:
            self.ret, self.frame = self.cap.read()

    def read(self):
        return self.ret, self.frame

    def stop(self):
        self.running = False
        self.cap.release()

    def isOpened(self):
        return self.cap.isOpened()


class VideoFileStream:
    def __init__(self, path):
        self.cap = cv2.VideoCapture(path)

    def read(self):
        return self.cap.read()

    def stop(self):
        self.cap.release()

    def isOpened(self):
        return self.cap.isOpened()


def open_camera(source, camera_id=0, width=320, height=240):
    if source == "picamera":
        return PiCameraStream(width, height)
    elif source == "usb":
        return USBCameraStream(camera_id, width, height)
    else:
        return VideoFileStream(source)
