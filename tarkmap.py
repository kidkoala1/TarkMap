import os
import re
import time
import threading
import math
from PIL import Image, ImageDraw, ImageTk
from tkinter import Tk, Label, messagebox
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# CONFIG 
SCREENSHOT_DIR = "" # Change to your directory, probably C:/Users/youruser/Documents/Escape From Tarkov/Screenshots
MAP_IMAGE = "customs.png" # Placeholder


# CALIBRATION (set to the included customs.png)
def world_to_pixel(x, z):
    scale_x = -3.933
    scale_z = 4.054
    min_x = 679.69
    min_z = -272.68
    px = int((x - min_x) * scale_x)
    py = int((z - min_z) * scale_z)
    return px, py

# EXTRACT COORDS + QUATERNION
def extract_data(filename):
    match = re.search(r'_([-+]?\d+\.\d+), [-+]?\d+\.\d+, ([-+]?\d+\.\d+)_([-+]?\d+\.\d+), ([-+]?\d+\.\d+), ([-+]?\d+\.\d+), ([-+]?\d+\.\d+)_', filename)
    if match:
        x = float(match.group(1))
        z = float(match.group(2))
        qx = float(match.group(3))
        qy = float(match.group(4))
        qz = float(match.group(5))
        qw = float(match.group(6))
        return x, z, (qx, qy, qz, qw)
    return None

# QUATERNION TO YAW
def quaternion_to_yaw(qx, qy, qz, qw):
    siny_cosp = 2 * (qw * qy + qx * qz)
    cosy_cosp = 1 - 2 * (qy * qy + qz * qz)
    return math.atan2(siny_cosp, cosy_cosp)

# DRAW FACING ARROW
def draw_facing(draw, px, py, yaw, length=20):
    yaw = -yaw
    end_x = px + length * math.cos(yaw)
    end_y = py + length * math.sin(yaw)
    draw.line((px, py, end_x, end_y), fill="red", width=3)



# GUI
class LiveMap:
    def __init__(self, root, map_path):
        self.root = root
        self.root.title("Tarkov Map Tracker")
        self.root.geometry("800x600")  # starting size
        self.root.minsize(400, 300)
        self.base_img = Image.open(map_path).convert("RGB")

        self.marker_pos = None  # (px, py)
        self.marker_yaw = None

        self.label = Label(self.root)
        self.label.pack(fill="both", expand=True)

        self.root.bind("<Configure>", self.on_resize)
        self.current_img = self.base_img.copy()
        self.update_display_image()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def on_close(self):
        answer = messagebox.askyesno("Clean up", "Delete ALL screenshots in folder? (This includes PREVIOUS (non TarkMap) screenshots!)")
        if answer:
            for f in os.listdir(SCREENSHOT_DIR):
                if f.lower().endswith(".png"):
                    try:
                        os.remove(os.path.join(SCREENSHOT_DIR, f))
                    except Exception as e:
                        print(f"failed to delete {f}: {e}")
        self.root.destroy()

    def update_display_image(self):
        # get current label size
        w = self.label.winfo_width()
        h = self.label.winfo_height()
        if w < 10 or h < 10:
            return  # window probably not ready yet

        # resize base image to fit label
        self.display_img = self.current_img.resize((w, h), Image.Resampling.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(self.display_img)
        self.label.config(image=self.tk_img)
        self.label.image = self.tk_img

    def draw_marker(self, px, py, yaw=None):
        self.marker_pos = (px, py)
        self.marker_yaw = yaw
        self.redraw()

    def redraw(self):
        # redraw base image
        self.current_img = self.base_img.copy()
        draw = ImageDraw.Draw(self.current_img)

        if self.marker_pos:
            # scale marker pos to current image size
            w_orig, h_orig = self.base_img.size
            w_disp = self.label.winfo_width()   
            h_disp = self.label.winfo_height()

            scale_x = w_orig / w_disp
            scale_y = h_orig / h_disp

            # inverse scale because we want px, py in original coords → scaled for display
            px_disp = int(self.marker_pos[0] * w_disp / w_orig)
            py_disp = int(self.marker_pos[1] * h_disp / h_orig)

            # draw on original sized image then rescale below
            draw.ellipse((self.marker_pos[0] - 20, self.marker_pos[1] - 20,
                          self.marker_pos[0] + 20, self.marker_pos[1] + 20), fill="red")
            if self.marker_yaw is not None:
                # draw arrow on original image
                length = 60
                yaw = self.marker_yaw
                yaw = yaw + math.pi
                end_x = self.marker_pos[0] + length * math.sin(yaw)
                end_y = self.marker_pos[1] - length * math.cos(yaw)
                draw.line((self.marker_pos[0], self.marker_pos[1], end_x, end_y), fill="red", width=12)

        self.update_display_image()

    def on_resize(self, event):
        # only redraw if marker exists
        if self.marker_pos:
            self.redraw()


# FILE WATCHER
class ScreenshotHandler(FileSystemEventHandler):
    def __init__(self, ui: LiveMap):
        self.ui = ui

    def on_created(self, event):
        if event.is_directory or not event.src_path.lower().endswith(".png"):
            return

        filename = os.path.basename(event.src_path)
        data = extract_data(filename)
        if not data:
            print(f"[!] failed to parse coords + rotation from: {filename}")
            return

        x, z, (qx, qy, qz, qw) = data
        px, py = world_to_pixel(x, z)
        yaw = quaternion_to_yaw(qx, qy, qz, qw)

        print(f"[+] {filename}: pixel ({px}, {py}), yaw {math.degrees(yaw):.1f}°")
        self.ui.root.after(0, self.ui.draw_marker, px, py, yaw)

# MAIN LOOP
def start_watching(ui):
    handler = ScreenshotHandler(ui)
    observer = Observer()
    observer.schedule(handler, SCREENSHOT_DIR, recursive=False)
    observer.start()
    print("[*] watching for new screenshots...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    root = Tk()
    app = LiveMap(root, MAP_IMAGE)

    thread = threading.Thread(target=start_watching, args=(app,), daemon=True)
    thread.start()

    root.mainloop()
