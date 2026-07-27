import cv2


class Camera:
    def __init__(self, source=0):
        self.cam = cv2.VideoCapture(source)

    def get_frame(self):
        success, frame = self.cam.read()
        if not success:
            return None
        return frame

    def release(self):
        self.cam.release()