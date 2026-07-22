from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import cv2
import os

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="template")

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


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

    img = cv2.imread(path)

    if filter_type == "grayscale":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        result = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    elif filter_type == "sepia":
        result = cv2.applyColorMap(img, cv2.COLORMAP_PINK)
    elif filter_type == "cartoon":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
        color = cv2.bilateralFilter(img, 9, 250, 250)
        result = cv2.bitwise_and(color, color, mask=edges)
    elif filter_type == "invert":
        result = cv2.bitwise_not(img)
    elif filter_type == "blur":
        result = cv2.GaussianBlur(img, (25, 25), 0)
    else:
        result = img

    out_filename = f"result_{file.filename}"
    out_path = f"uploads/{out_filename}"
    cv2.imwrite(out_path, result)

    return templates.TemplateResponse(request, "home.html", {
        "raw": f"uploads/{file.filename}",
        "result": f"uploads/{out_filename}"
    })