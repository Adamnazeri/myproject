from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import cv2
import os
from filter import Filter
from camera import Camera
from auth import Auth, DEPARTMENTS

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="filterstudio2026secret")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="template")

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

VIDEO_EXT = (".mp4", ".mov", ".avi", ".mkv")

object = Filter()
camera_instance = Camera()
auth = Auth()


def get_profile(request: Request):
    username = request.session.get("user")
    if not username:
        return None
    return auth.get_user_info(username)


# ============ AUTHENTICATION ROUTES ============

@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse(request, "signup.html", {"error": None, "departments": DEPARTMENTS})


@app.post("/signup", response_class=HTMLResponse)
def signup_submit(request: Request, username: str = Form(...), password: str = Form(...),
                   confirm_password: str = Form(...), phone: str = Form(...), dept: str = Form(...)):
    if len(username.strip()) < 3:
        return templates.TemplateResponse(request, "signup.html", {
            "error": "Username must be at least 3 characters", "departments": DEPARTMENTS
        })
    if len(password) < 6:
        return templates.TemplateResponse(request, "signup.html", {
            "error": "Password must be at least 6 characters", "departments": DEPARTMENTS
        })
    if password != confirm_password:
        return templates.TemplateResponse(request, "signup.html", {
            "error": "Password and Confirm Password do not match", "departments": DEPARTMENTS
        })
    if dept not in DEPARTMENTS:
        return templates.TemplateResponse(request, "signup.html", {
            "error": "Please select a valid department", "departments": DEPARTMENTS
        })

    success = auth.register(username.strip(), password, phone.strip(), dept)
    if success:
        return RedirectResponse(url="/login?registered=1", status_code=303)
    return templates.TemplateResponse(request, "signup.html", {
        "error": "Username already exists, please choose another", "departments": DEPARTMENTS
    })


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, registered: str = None):
    success_msg = "Registration successful! Please log in." if registered else None
    return templates.TemplateResponse(request, "login.html", {"error": None, "success": success_msg})


@app.post("/login", response_class=HTMLResponse)
def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    if auth.check_password(username, password):
        request.session["user"] = username
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request, "login.html", {
        "error": "Invalid username or password", "success": None
    })


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


# ============ PROFILE PICTURE (BLOB) ============

@app.post("/profile/upload_pic")
async def upload_profile_pic(request: Request, pic: UploadFile = File(...)):
    username = request.session.get("user")
    if not username:
        return RedirectResponse(url="/login", status_code=303)

    image_bytes = await pic.read()
    auth.update_profile_pic(username, image_bytes)

    return RedirectResponse(url="/", status_code=303)


@app.get("/profile/pic/{username}")
def get_profile_pic(username: str):
    image_bytes = auth.get_profile_pic(username)
    if image_bytes is None:
        return Response(status_code=204)
    return Response(content=image_bytes, media_type="image/jpeg")


# ============ EDIT PROFILE ============

@app.get("/profile/edit", response_class=HTMLResponse)
def edit_profile_page(request: Request):
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "edit_profile.html", {
        "profile": get_profile(request), "departments": DEPARTMENTS, "error": None, "success": None
    })


@app.post("/profile/edit", response_class=HTMLResponse)
def edit_profile_submit(request: Request, username: str = Form(...), phone: str = Form(...), dept: str = Form(...)):
    old_username = request.session.get("user")
    if not old_username:
        return RedirectResponse(url="/login", status_code=303)

    if len(username.strip()) < 3:
        return templates.TemplateResponse(request, "edit_profile.html", {
            "profile": get_profile(request), "departments": DEPARTMENTS,
            "error": "Username must be at least 3 characters", "success": None
        })
    if dept not in DEPARTMENTS:
        return templates.TemplateResponse(request, "edit_profile.html", {
            "profile": get_profile(request), "departments": DEPARTMENTS,
            "error": "Please select a valid department", "success": None
        })

    success = auth.update_profile(old_username, username.strip(), phone.strip(), dept)
    if success:
        request.session["user"] = username.strip()
        return templates.TemplateResponse(request, "edit_profile.html", {
            "profile": get_profile(request), "departments": DEPARTMENTS,
            "error": None, "success": "Profile updated successfully!"
        })
    return templates.TemplateResponse(request, "edit_profile.html", {
        "profile": get_profile(request), "departments": DEPARTMENTS,
        "error": "That username is already taken", "success": None
    })


@app.post("/profile/change_password", response_class=HTMLResponse)
def change_password_submit(request: Request, current_password: str = Form(...),
                             new_password: str = Form(...), confirm_new_password: str = Form(...)):
    username = request.session.get("user")
    if not username:
        return RedirectResponse(url="/login", status_code=303)

    if not auth.check_password(username, current_password):
        return templates.TemplateResponse(request, "edit_profile.html", {
            "profile": get_profile(request), "departments": DEPARTMENTS,
            "error": "Current password is incorrect", "success": None
        })
    if len(new_password) < 6:
        return templates.TemplateResponse(request, "edit_profile.html", {
            "profile": get_profile(request), "departments": DEPARTMENTS,
            "error": "New password must be at least 6 characters", "success": None
        })
    if new_password != confirm_new_password:
        return templates.TemplateResponse(request, "edit_profile.html", {
            "profile": get_profile(request), "departments": DEPARTMENTS,
            "error": "New password and confirmation do not match", "success": None
        })

    auth.update_password(username, new_password)
    return templates.TemplateResponse(request, "edit_profile.html", {
        "profile": get_profile(request), "departments": DEPARTMENTS,
        "error": None, "success": "Password changed successfully!"
    })


# ============ MAIN ROUTES (Protected) ============

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "home.html", {"result": None, "profile": get_profile(request)})


@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "about.html", {"profile": get_profile(request)})


@app.post("/", response_class=HTMLResponse)
async def upload(request: Request, file: UploadFile = File(...), filter_type: str = Form(...)):
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=303)

    for old_file in os.listdir("uploads"):
        old_path = os.path.join("uploads", old_file)
        try:
            if os.path.isfile(old_path):
                os.remove(old_path)
        except Exception as e:
            print(f"Could not delete {old_path}: {e}")

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
        "is_video": is_video,
        "profile": get_profile(request)
    })


@app.get("/webcam", response_class=HTMLResponse)
def webcam_page(request: Request):
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "webcam.html", {
        "is_running": camera_instance.is_running, "profile": get_profile(request)
    })


@app.post("/camera/start")
def camera_start():
    camera_instance.start()
    return {"status": "started", "is_running": camera_instance.is_running}


@app.post("/camera/stop")
def camera_stop():
    camera_instance.stop()
    return {"status": "stopped", "is_running": camera_instance.is_running}


def gen_frames(filter_type):
    while camera_instance.is_running:
        frame = camera_instance.get_frame()
        if frame is None:
            continue
        if filter_type and filter_type != "none":
            processed = object.filter(frame, filter_type)
        else:
            processed = frame
        ret, buffer = cv2.imencode(".jpg", processed)
        frame_bytes = buffer.tobytes()
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")


@app.get("/video_feed")
def video_feed(filter_type: str = "none"):
    return StreamingResponse(gen_frames(filter_type), media_type="multipart/x-mixed-replace; boundary=frame")
