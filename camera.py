import cv2
import threading


class Camera:
    def __init__(self, source=0):
        self.source = source
        self.cam = None
        self.is_running = False
        self.latest_frame = None
        self.lock = threading.Lock()
        self.thread = None

    def start(self):
        if not self.is_running:
            self.cam = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
            self.is_running = True
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()

    def _capture_loop(self):
        while self.is_running:
            success, frame = self.cam.read()
            if not success:
                break
            with self.lock:
                self.latest_frame = frame

    def stop(self):
        if self.is_running:
            self.is_running = False
            if self.thread is not None:
                self.thread.join(timeout=2)
            if self.cam is not None:
                self.cam.release()
            self.latest_frame = None

    def get_frame(self):
        if not self.is_running:
            return None
        with self.lock:
            return self.latest_frame