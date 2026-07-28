import cv2                          # Import OpenCV — library untuk proses gambar/video
from ultralytics import YOLO        # Import model YOLO untuk object detection


class Filter:                       # Definisi class — blueprint untuk semua fungsi filter
    def __init__(self):             # Constructor — jalan sekali sahaja bila object dicipta
        self.yolo_model = YOLO("yolov8n.pt")   # Load model YOLO, simpan dalam object (self)

    def filter(self, img, filter_type):        # Method utama — terima gambar & jenis filter
        if filter_type == "grayscale":         # Kalau user pilih "grayscale"
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)         # Tukar gambar jadi hitam-putih
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)        # Tukar balik ke format 3-channel supaya boleh papar

        elif filter_type == "sepia":           # Kalau user pilih "sepia"
            return cv2.applyColorMap(img, cv2.COLORMAP_PINK)     # Apply warna tone pink/sepia

        elif filter_type == "cartoon":         # Kalau user pilih "cartoon"
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)         # Tukar hitam-putih dulu
            gray = cv2.medianBlur(gray, 5)                       # Buang noise kecil (haluskan)
            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)  # Detect garis tepi
            color = cv2.bilateralFilter(img, 9, 250, 250)        # Ratakan warna asal (smooth tapi tepi tajam)
            return cv2.bitwise_and(color, color, mask=edges)     # Gabung warna rata + garis tepi = kartun

        elif filter_type == "invert":          # Kalau user pilih "invert"
            return cv2.bitwise_not(img)                          # Songsang setiap nilai pixel (macam negative filem)

        elif filter_type == "blur":            # Kalau user pilih "blur"
            return cv2.GaussianBlur(img, (25, 25), 0)            # Kaburkan gambar guna kernel 25x25

        elif filter_type == "yolo":            # Kalau user pilih "yolo" (AI object detection)
            results = self.yolo_model(img, verbose=False)        # Hantar gambar ke model YOLO untuk predict
            return results[0].plot()                             # Lukis kotak + label atas gambar, return hasil

        else:                                   # Kalau filter_type tak match apa-apa di atas
            return img                                           # Return gambar asal tanpa ubah apa-apa