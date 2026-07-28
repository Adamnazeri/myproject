from fastapi import FastAPI, Request, UploadFile, File, Form   # Import komponen FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse  # Import jenis response (HTML biasa & streaming)
from fastapi.templating import Jinja2Templates                 # Import engine untuk render fail HTML
from fastapi.staticfiles import StaticFiles                    # Import untuk serve fail statik (CSS, gambar)
import cv2                          # Import OpenCV
import os                           # Import untuk urus fail & folder sistem
from filter import Filter           # Import class Filter dari fail filter.py
from camera import Camera           # Import class Camera dari fail camera.py

app = FastAPI()                     # Cipta object app — "otak utama" server

app.mount("/static", StaticFiles(directory="static"), name="static")   # Sambung URL /static ke folder static/
templates = Jinja2Templates(directory="template")                       # Setup engine render HTML dari folder template/

os.makedirs("uploads", exist_ok=True)          # Cipta folder uploads kalau belum wujud
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads") # Sambung URL /uploads ke folder uploads/

VIDEO_EXT = (".mp4", ".mov", ".avi", ".mkv")   # Senarai extension yang dianggap video

# ================================
# INITIALIZATION — cipta object dari class Filter (sekali sahaja, semasa server start)
# ================================
object = Filter()                   # object sekarang ialah instance sebenar dari class Filter
                                     # Bila baris ni jalan, __init__ dalam Filter auto-panggil (load YOLO)


@app.get("/", response_class=HTMLResponse)       # Route: bila browser request GET ke "/"
def home(request: Request):                      # Function yang jalan bila route ni dipanggil
    return templates.TemplateResponse(request, "home.html", {"result": None})  # Papar home.html, result kosong

    # Function ni handle page utama (upload page), tanpa data hasil lagi


@app.get("/about", response_class=HTMLResponse)  # Route: bila browser request GET ke "/about"
def about(request: Request):
    return templates.TemplateResponse(request, "about.html")   # Papar about.html sahaja


@app.post("/", response_class=HTMLResponse)      # Route: bila browser request POST ke "/" (submit form)
async def upload(request: Request, file: UploadFile = File(...), filter_type: str = Form(...)):
    # file = fail yang di-upload, filter_type = pilihan dropdown

    # --- Padam semua fail lama dalam folder uploads ---
    for old_file in os.listdir("uploads"):        # Loop setiap nama fail dalam folder uploads
        old_path = os.path.join("uploads", old_file)   # Bina path penuh untuk fail tu
        try:
            if os.path.isfile(old_path):            # Pastikan ia memang fail (bukan folder)
                os.remove(old_path)                 # Padam fail tu
        except Exception as e:                      # Kalau ada masalah semasa padam
            print(f"Tak boleh padam {old_path}: {e}")   # Print mesej error, tak crash app

    # --- Simpan fail baru yang di-upload ---
    path = f"uploads/{file.filename}"              # Bina lokasi simpan (contoh: uploads/gambar.jpg)
    with open(path, "wb") as f:                     # Buka fail baru dalam mode "write binary"
        f.write(await file.read())                  # Baca kandungan fail upload, tulis ke fail baru

    # --- Check jenis fail: video atau gambar ---
    ext = os.path.splitext(file.filename)[1].lower()   # Ambil extension fail (contoh: .mp4), huruf kecil
    is_video = ext in VIDEO_EXT                          # True kalau extension tu dalam senarai video

    if is_video:                                    # === PROSES VIDEO ===
        temp_filename = f"temp_{os.path.splitext(file.filename)[0]}.mp4"   # Nama fail sementara
        temp_path = f"uploads/{temp_filename}"
        out_filename = f"result_{os.path.splitext(file.filename)[0]}.mp4"  # Nama fail hasil akhir
        out_path = f"uploads/{out_filename}"

        cap = cv2.VideoCapture(path)                # Buka video asal untuk dibaca
        fps = cap.get(cv2.CAP_PROP_FPS) or 20        # Ambil frame rate asal (default 20 kalau gagal)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))   # Ambil lebar video
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # Ambil tinggi video
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")     # Set codec untuk fail output (mp4v = built-in)
        writer = cv2.VideoWriter(temp_path, fourcc, fps, (w, h))   # Setup "penulis" video baru

        while True:                                  # Loop proses setiap frame video
            ret, frame = cap.read()                  # Ambil satu frame; ret = True/False
            if not ret:                              # Kalau video dah habis
                break                                # Keluar loop
            processed = object.filter(frame, filter_type)   # PANGGIL METHOD FILTER — proses frame ni
            writer.write(processed)                  # Tulis frame yang dah diproses ke fail baru

        cap.release()                                # Tutup sambungan video asal
        writer.release()                             # Tutup fail video baru (simpan sepenuhnya)

        # --- Convert codec supaya browser boleh play ---
        import imageio_ffmpeg                        # Import package untuk dapatkan ffmpeg
        import subprocess                             # Import untuk jalankan command line

        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()  # Dapatkan lokasi program ffmpeg
        subprocess.run([                              # Jalankan ffmpeg untuk convert codec
            ffmpeg_exe, "-y", "-i", temp_path,
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            out_path
        ], check=True)
        os.remove(temp_path)                          # Padam fail sementara (dah tak diperlukan)

    else:                                             # === PROSES GAMBAR ===
        out_filename = f"result_{file.filename}"      # Nama fail hasil
        out_path = f"uploads/{out_filename}"
        img = cv2.imread(path)                        # Baca fail gambar jadi array
        result = object.filter(img, filter_type)       # PANGGIL METHOD FILTER — proses gambar ni
        cv2.imwrite(out_path, result)                  # Simpan gambar hasil ke fail baru

    # --- Papar semula page dengan hasil ---
    return templates.TemplateResponse(request, "home.html", {
        "raw": f"uploads/{file.filename}",             # Path gambar/video asal
        "result": f"uploads/{out_filename}",           # Path gambar/video hasil
        "is_video": is_video                            # True/False — untuk HTML tahu papar <video> atau <img>
    })


def gen_frames(filter_type):                          # Function generator untuk streaming webcam
    camera_object = Camera()                           # Cipta OBJECT baru dari class Camera (buka webcam)
    while True:                                        # Loop tak henti — proses setiap frame webcam
        frame = camera_object.get_frame()               # PANGGIL METHOD get_frame — ambil satu gambar
        if frame is None:                               # Kalau webcam gagal (tiada gambar)
            break                                        # Keluar loop
        if filter_type and filter_type != "none":       # Kalau ada filter dipilih (bukan "none")
            processed = object.filter(frame, filter_type)  # PANGGIL METHOD FILTER — proses frame webcam
        else:                                            # Kalau tiada filter
            processed = frame                             # Guna gambar asal
        ret, buffer = cv2.imencode(".jpg", processed)     # Tukar gambar jadi format JPEG bytes
        frame_bytes = buffer.tobytes()                     # Convert jadi bytes murni
        yield (b"--frame\r\n"                              # Hantar satu "chunk" data ke browser (streaming)
               b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
    camera_object.release()                             # PANGGIL METHOD release — tutup webcam bila loop tamat


@app.get("/webcam", response_class=HTMLResponse)       # Route: bila browser request GET ke "/webcam"
def webcam_page(request: Request):
    return templates.TemplateResponse(request, "webcam.html")   # Papar page webcam.html


@app.get("/video_feed")                                 # Route: untuk streaming video dari webcam
def video_feed(filter_type: str = "none"):               # filter_type diambil dari query URL (?filter_type=...)
    return StreamingResponse(gen_frames(filter_type), media_type="multipart/x-mixed-replace; boundary=frame")
    # StreamingResponse — hantar data secara berterusan (bukan sekali sahaja) ke browser