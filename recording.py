import cv2
import threading
import os
import subprocess
import time
import imageio_ffmpeg
from datetime import datetime
from filter import Filter


class Recording:
    def __init__(self, camera, filter_processor=None):
        self.camera = camera
        self.filter_processor = filter_processor or Filter()
        self.is_recording = False
        self.lock = threading.Lock()
        self.thread = None
        self.writer = None
        self.temp_path = None
        self.final_path = None
        self.filter_type = "none"
        self.target_fps = 20

    def _get_output_folder(self):
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        folder = os.path.join("runs", "recording", year, month)
        os.makedirs(folder, exist_ok=True)
        return folder

    def start(self, fps=20, filter_type="none"):
        with self.lock:
            if self.is_recording:
                return None
            if not self.camera.is_running:
                return None

            self.filter_type = filter_type or "none"
            self.target_fps = max(1, fps)

            folder = self._get_output_folder()
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"recording_{timestamp}"

            self.temp_path = os.path.join(folder, f"temp_{filename}.mp4")
            self.final_path = os.path.join(folder, f"{filename}.mp4")

            frame = self.camera.get_frame()
            if frame is None:
                return None
            h, w = frame.shape[:2]

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self.writer = cv2.VideoWriter(self.temp_path, fourcc, fps, (w, h))

            self.is_recording = True
            self.thread = threading.Thread(target=self._record_loop, daemon=True)
            self.thread.start()

            return self.final_path

    def _record_loop(self):
        interval = 1.0 / self.target_fps
        next_time = time.perf_counter()

        while self.is_recording:
            now = time.perf_counter()
            if now < next_time:
                time.sleep(0.001)
                continue

            frame = self.camera.get_frame()
            if frame is not None:
                if self.filter_type and self.filter_type != "none":
                    frame_to_write = self.filter_processor.filter(frame, self.filter_type)
                else:
                    frame_to_write = frame
                self.writer.write(frame_to_write)

            next_time = now + interval

    def stop(self):
        with self.lock:
            if not self.is_recording:
                return None
            self.is_recording = False

        if self.thread is not None:
            self.thread.join(timeout=3)

        if self.writer is not None:
            self.writer.release()

        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run([
            ffmpeg_exe, "-y", "-i", self.temp_path,
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            self.final_path
        ], check=True)

        os.remove(self.temp_path)

        result_path = self.final_path
        self.temp_path = None
        self.final_path = None
        return result_path