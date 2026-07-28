import cv2                          # Import OpenCV


class Camera:                       # Blueprint untuk kendalikan webcam
    def __init__(self, source=0):   # Constructor — source=0 = webcam default
        self.cam = cv2.VideoCapture(source)

    def get_frame(self):            # Ambil satu frame dari webcam
        success, frame = self.cam.read()
        if not success:
            return None
        return frame

    def release(self):              # Tutup sambungan webcam
        self.cam.release()