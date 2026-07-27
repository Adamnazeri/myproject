import cv2
from ultralytics import YOLO


class Filter:
    def __init__(self):
        self.yolo_model = YOLO("yolov8n.pt")

    def filter(self, img, filter_type):
        if filter_type == "grayscale":
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        elif filter_type == "sepia":
            return cv2.applyColorMap(img, cv2.COLORMAP_PINK)
        elif filter_type == "cartoon":
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.medianBlur(gray, 5)
            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
            color = cv2.bilateralFilter(img, 9, 250, 250)
            return cv2.bitwise_and(color, color, mask=edges)
        elif filter_type == "invert":
            return cv2.bitwise_not(img)
        elif filter_type == "blur":
            return cv2.GaussianBlur(img, (25, 25), 0)
        elif filter_type == "yolo":
            results = self.yolo_model(img, verbose=False)
            return results[0].plot()
        else:
            return img