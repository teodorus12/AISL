import tkinter as tk
from HT_video import VPanel


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HT_V2")
        self.root.geometry("1200x800")

        self.video_panel = VPanel(self.root)

    def update_video(self, frame):
        self.video_panel.update(frame)

    def after(self, delay, callback):
        self.root.after(delay, callback)

    def set_close_callback(self, callback):
        self.root.protocol("WM_DELETE_WINDOW", callback)

    def start(self):
        self.root.mainloop()

    def destroy(self):
        self.root.destroy()