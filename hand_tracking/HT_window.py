import tkinter as tk
from hand_tracking.HT_video import VPanel

SIDEBAR_WIDTH = 300


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HT_V2")
        self.root.geometry("1100x700")
        self.root.minsize(900, 500)

        self.container = tk.Frame(self.root)
        self.container.pack(expand=True, fill="both")
        self.container.columnconfigure(0, weight=1, minsize=500)
        self.container.columnconfigure(1, weight=0, minsize=SIDEBAR_WIDTH)
        self.container.rowconfigure(0, weight=1)

        self.left = tk.Frame(self.container)
        self.left.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        self.video_panel = VPanel(self.left)
        
        self.text_area = tk.Frame(self.left)
        self.text = tk.StringVar(value="")
        self.text_var = tk.StringVar(value="Trenutno besedilo:")
        tk.Label(self.left, textvariable=self.text_var, justify="center").pack(pady=8, padx=8)

        tk.Button(self.left, text="CLEAR - Text", command=self.clear_text(),
        ).pack(pady=1)
        tk.Button(self.left, text="CLEAR - last letter", command=self.clear_previous_letter,
        ).pack(pady=1)


        self.right = tk.Frame(self.container, width=SIDEBAR_WIDTH, bg="#f5f5f5")
        self.right.grid(row=0, column=1, sticky="ns")
        self.right.grid_propagate(False)

        tk.Label(
            self.right,
            text="Hand Tracking",
            font=("Helvetica", 16, "bold"),
            bg="#f5f5f5",
        ).pack(pady=(24, 8))

        self.lbl_var = tk.StringVar(value="Trenutni znak: A")
        tk.Label(
            self.right,
            textvariable=self.lbl_var,
            font=("Helvetica", 14),
            bg="#f5f5f5",
            wraplength=SIDEBAR_WIDTH - 24,
            justify="center",
        ).pack(pady=16)

        self.pred_var = tk.StringVar(value="AI: —")
        tk.Label(
            self.right,
            textvariable=self.pred_var,
            font=("Helvetica", 22, "bold"),
            bg="#f5f5f5",
            wraplength=SIDEBAR_WIDTH - 24,
            justify="center",
        ).pack(pady=16)

        tk.Label(
            self.right,
            text="Pritisni črko (A–Z)\nza oznako posnetka",
            font=("Helvetica", 11),
            bg="#f5f5f5",
            justify="center",
        ).pack(pady=8)

        tk.Button(
            self.right,
            text="SHUT DOWN - HT",
            command=self.destroy,
        ).pack(side="bottom", pady=16)

    def set_lbl(self, lbl):
        v = lbl.upper()
        if v:
            self.lbl_var.set(f"Trenutni znak: {v.upper()}")
            
    def set_text(self, lbl):
        v = lbl.upper()
        if v:
            self.text_var.set(f"Trenutno besedilo: {v}")
            
    def build_text(self, letter):
        curr_text = self.text.get()
        if letter == "?":
            return
        if not curr_text or curr_text[-1] != letter:
            text = self.text.get() + letter
            self.text.set(text)
            self.set_text(text)
        
    def clear_text(self):
        self.text.set("")
        self.text_var.set(f"Trenutno besedilo: ")
        
    def clear_previous_letter(self):
        curr_text = self.text.get()
    
        if curr_text:
            text = curr_text[:-1]
            self.text.set(text)
            self.set_text(text)
        

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

    def set_prediction(self, label: str, confidence: float):
        pct = int(confidence * 100)
        self.pred_var.set(f"AI: {label}\n({pct}%)")
