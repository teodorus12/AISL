import tkinter as tkr
import cv2
from PIL import Image, ImageTk

class VPanel:
    def __init__(self, root):
        self.label = tkr.Label(root)
        self.label.pack(fill="both", expand=True)
        
    def update(self, frame):
        rgber = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgber)
        
        photo = ImageTk.PhotoImage(image=img)
        self.label.configure(image=photo)
        self.label.image = photo