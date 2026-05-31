import tkinter as tk
from hand_tracking.HT_video import VPanel

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HT_V2")
        self.root.geometry("1200x800")
        
        self.container = tk.Frame(self.root)
        self.container.pack(expand=True, fill="both")
        self.container.columnconfigure(0, weight=3)
        self.container.columnconfigure(1, weight=1)
        self.container.rowconfigure(0, weight=1)
        
        self.left = tk.Frame(self.container)
        self.left.grid(row=0, column=0, sticky="nsew")
        self.video_panel = VPanel(self.left)
        
        self.right = tk.Frame(self.container)
        self.right.grid(row=0, column=1, sticky="nsew")
        self.right.grid_propagate(False)

        self.lbl_var = tk.StringVar(value="Trenutni znak: A")
        self.curr_lbl = tk.Label(self.right, textvariable=self.lbl_var).pack(pady=40)

        # ── AI prediction display ──
        self.pred_var = tk.StringVar(value="AI: —")
        tk.Label(self.right, textvariable=self.pred_var, font=("Helvetica", 28, "bold")).pack(pady=20)

        tk.Label(self.right, text="Oznaka").pack(pady=10)
        tk.Button(self.right, text="SHUT DOWN - HT", command=self.destroy).pack(side="bottom", pady=10)

    def set_lbl(self, lbl):
        v = lbl.upper()
        if v:
            self.lbl_var.set(f"Trenutni znak: {v.upper()}")

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

    # ── AI prediction display ──
    def set_prediction(self, label: str, confidence: float):
        pct = int(confidence * 100)
        self.pred_var.set(f"AI: {label}  ({pct}%)")