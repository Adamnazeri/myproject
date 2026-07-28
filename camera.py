import cv2                          # Import OpenCV


class Camera:                       # Definisi class — blueprint untuk kendalikan webcam
    def __init__(self, source=0):   # Constructor — source=0 bermaksud webcam default (laptop)
        self.cam = cv2.VideoCapture(source)    # Buka sambungan ke webcam, simpan dalam object

    def get_frame(self):            # Method untuk ambil SATU gambar/frame dari webcam
        success, frame = self.cam.read()       # Baca satu frame; success = True/False
        if not success:              # Kalau gagal ambil frame
            return None                          # Return None supaya code luar tahu ada masalah
        return frame                 # Kalau berjaya, return gambar tu

    def release(self):              # Method untuk tutup sambungan webcam
        self.cam.release()                        # Lepaskan webcam supaya app lain boleh guna