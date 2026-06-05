import tkinter as tkr
import cv2
from PIL import Image, ImageTk

'''
    This class creates a field where the current camera output is displayed.
'''


class VPanel:
    def __init__(self, root):
        self.root = root
        self.label = tkr.Label(root)
        self.label.pack(fill="both", expand=True)
        self.max_w = 960
        self.max_h = 540
        root.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        if event.widget is self.root and event.width > 1 and event.height > 1:
            self.max_w = event.width
            self.max_h = event.height

    def update(self, frame):
        h, w = frame.shape[:2]
        scale = min(self.max_w / w, self.max_h / h)
        if scale < 1.0:
            new_w = max(int(w * scale), 1)
            new_h = max(int(h * scale), 1)
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

        rgber = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgber)

        photo = ImageTk.PhotoImage(image=img)
        self.label.configure(image=photo)
        self.label.image = photo
