import cv2


class Camera:
    def __init__(self, source=0):
        self.source = source
        self.cam = None
        self.is_running = False

    def start(self):
        if not self.is_running:
            self.cam = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
            self.is_running = True

    def stop(self):
        if self.is_running and self.cam is not None:
            self.cam.release()
            self.is_running = False    # flag/condition - status camera is running or not

    def get_frame(self):
        if not self.is_running or self.cam is None:
            return None
        success, frame = self.cam.read()
        if not success:
            return None
        return frame