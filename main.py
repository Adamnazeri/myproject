from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import cv2
import os
from ultralytics import YOLO

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="template")

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

VIDEO_EXT = (".mp4", ".mov", ".avi", ".mkv")

yolo_model = YOLO("yolov8n.pt")


def apply_filter_frame(img, filter_type):
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
        results = yolo_model(img, verbose=False)
        return results[0].plot()
    else:
        return img


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"result": None})


@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse(request, "about.html")


@app.post("/", response_class=HTMLResponse)
async def upload(request: Request, file: UploadFile = File(...), filter_type: str = Form(...)):
    path = f"uploads/{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())

    ext = os.path.splitext(file.filename)[1].lower()
    is_video = ext in VIDEO_EXT

    if is_video:
        out_filename = f"result_{os.path.splitext(file.filename)[0]}.mp4"
        out_path = f"uploads/{out_filename}"

        cap = cv2.VideoCapture(path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 20
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*"avc1")
        writer = cv2.VideoWriter(out_path, fourcc, fps, (w, h))

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            processed = apply_filter_frame(frame, filter_type)
            writer.write(processed)

        cap.release()
        writer.release()
    else:
        out_filename = f"result_{file.filename}"
        out_path = f"uploads/{out_filename}"
        img = cv2.imread(path)
        result = apply_filter_frame(img, filter_type)
        cv2.imwrite(out_path, result)

    return templates.TemplateResponse(request, "home.html", {
        "raw": f"uploads/{file.filename}",
        "result": f"uploads/{out_filename}",
        "is_video": is_video
    })