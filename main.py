from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import cv2
import os
from filter import Filter
from camera import Camera

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="template")

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

VIDEO_EXT = (".mp4", ".mov", ".avi", ".mkv")

# Object — instance dicipta dari class Filter
object = Filter()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"result": None})


@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse(request, "about.html")


@app.post("/", response_class=HTMLResponse)
async def upload(request: Request, file: UploadFile = File(...), filter_type: str = Form(...)):
    for old_file in os.listdir("uploads"):
        old_path = os.path.join("uploads", old_file)
        try:
            if os.path.isfile(old_path):
                os.remove(old_path)
        except Exception as e:
            print(f"Tak boleh padam {old_path}: {e}")

    path = f"uploads/{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())

    ext = os.path.splitext(file.filename)[1].lower()
    is_video = ext in VIDEO_EXT

    if is_video:
        temp_filename = f"temp_{os.path.splitext(file.filename)[0]}.mp4"
        temp_path = f"uploads/{temp_filename}"
        out_filename = f"result_{os.path.splitext(file.filename)[0]}.mp4"
        out_path = f"uploads/{out_filename}"

        cap = cv2.VideoCapture(path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 20
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(temp_path, fourcc, fps, (w, h))

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            processed = object.filter(frame, filter_type)
            writer.write(processed)

        cap.release()
        writer.release()

        import imageio_ffmpeg
        import subprocess

        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run([
            ffmpeg_exe, "-y", "-i", temp_path,
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            out_path
        ], check=True)
        os.remove(temp_path)
    else:
        out_filename = f"result_{file.filename}"
        out_path = f"uploads/{out_filename}"
        img = cv2.imread(path)
        result = object.filter(img, filter_type)
        cv2.imwrite(out_path, result)

    return templates.TemplateResponse(request, "home.html", {
        "raw": f"uploads/{file.filename}",
        "result": f"uploads/{out_filename}",
        "is_video": is_video
    })


def gen_frames(filter_type):
    camera_object = Camera()
    while True:
        frame = camera_object.get_frame()
        if frame is None:
            break
        if filter_type and filter_type != "none":
            processed = object.filter(frame, filter_type)
        else:
            processed = frame
        ret, buffer = cv2.imencode(".jpg", processed)
        frame_bytes = buffer.tobytes()
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
    camera_object.release()


@app.get("/webcam", response_class=HTMLResponse)
def webcam_page(request: Request):
    return templates.TemplateResponse(request, "webcam.html")


@app.get("/video_feed")
def video_feed(filter_type: str = "none"):
    return StreamingResponse(gen_frames(filter_type), media_type="multipart/x-mixed-replace; boundary=frame")
