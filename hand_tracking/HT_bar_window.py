import tkinter as tk
from tkinter import ttk
import unicodedata

from hand_tracking.HT_video import VPanel

SIDEBAR_WIDTH = 360
BG = "#f4efe7"
CARD = "#ffffff"
INK = "#221b14"
MUTED = "#6f6256"
ACCENT = "#8b4a22"
ACCENT_DARK = "#5f3218"
SOFT = "#f7e6d6"
BORDER = "#ead8c6"
HIGHLIGHT = "#d4a574"

MENU_ITEMS = ("Kava", "Čaj", "Sok", "Pivo", "Vino")


class BarDemoWindow:
    def __init__(
        self,
        wav_files: list[str],
        on_refresh,
        on_predict,
        on_play_wav,
        on_play_signs,
        on_fetch_stm32,
    ):
        self.root = tk.Tk()
        self.root.title("Bar brez ovir")
        self.root.geometry("1240x820")
        self.root.minsize(1020, 640)
        self.root.configure(bg=BG)

        self._on_refresh = on_refresh
        self._on_predict = on_predict
        self._on_play_wav = on_play_wav
        self._on_play_signs = on_play_signs
        self._on_fetch_stm32 = on_fetch_stm32
        self._menu_labels: dict[str, tk.Label] = {}
        self._fetch_btn: tk.Button | None = None

        outer = tk.Frame(self.root, bg=BG)
        outer.pack(expand=True, fill="both", padx=16, pady=14)

        self._build_header(outer)
        self._build_main(outer, wav_files)
        self._build_footer(outer)

    def _build_header(self, parent: tk.Frame) -> None:
        header = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        header.pack(fill="x", pady=(0, 12))

        top_row = tk.Frame(header, bg=CARD)
        top_row.pack(fill="x", padx=20, pady=(16, 8))

        tk.Label(
            top_row,
            text="Bar brez ovir",
            font=("Helvetica", 26, "bold"),
            bg=CARD,
            fg=INK,
        ).pack(side="left")

        tk.Label(
            top_row,
            text="Avtonomno naročanje · govor · znakovni jezik",
            font=("Helvetica", 11),
            bg=CARD,
            fg=MUTED,
        ).pack(side="left", padx=(16, 0))

        menu_wrap = tk.Frame(header, bg=SOFT)
        menu_wrap.pack(fill="x", padx=16, pady=(0, 16))

        tk.Label(
            menu_wrap,
            text="MENI",
            font=("Helvetica", 12, "bold"),
            bg=SOFT,
            fg=ACCENT_DARK,
        ).pack(anchor="w", padx=12, pady=(10, 6))

        menu_row = tk.Frame(menu_wrap, bg=SOFT)
        menu_row.pack(fill="x", padx=8, pady=(0, 10))

        for i, item in enumerate(MENU_ITEMS):
            cell = tk.Frame(
                menu_row,
                bg=CARD,
                highlightbackground=BORDER,
                highlightthickness=1,
            )
            cell.grid(row=0, column=i, padx=6, pady=4, sticky="nsew")
            menu_row.columnconfigure(i, weight=1)

            lbl = tk.Label(
                cell,
                text=item.upper(),
                font=("Helvetica", 14, "bold"),
                bg=CARD,
                fg=ACCENT_DARK,
                pady=14,
            )
            lbl.pack(fill="both", expand=True)
            self._menu_labels[item.lower()] = lbl

    def _build_main(self, parent: tk.Frame, wav_files: list[str]) -> None:
        main = tk.Frame(parent, bg=BG)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1, minsize=540)
        main.columnconfigure(1, weight=0, minsize=SIDEBAR_WIDTH)
        main.rowconfigure(0, weight=1)

        left = tk.Frame(main, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.rowconfigure(1, weight=1)
        left.rowconfigure(2, weight=0)
        left.columnconfigure(0, weight=1)

        tk.Label(
            left,
            text="Znakovni jezik — live prepoznava",
            font=("Helvetica", 13, "bold"),
            bg=CARD,
            fg=INK,
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 6))

        video_host = tk.Frame(left, bg="#111111")
        video_host.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))
        self.video_panel = VPanel(video_host)

        text_panel = tk.Frame(left, bg=CARD)
        text_panel.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        text_panel.columnconfigure(0, weight=1)

        self._text = tk.StringVar(value="")
        self.text_var = tk.StringVar(value="Trenutno besedilo:")
        text_box = tk.Frame(text_panel, bg=SOFT, highlightbackground=BORDER, highlightthickness=1)
        text_box.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        tk.Label(
            text_box,
            textvariable=self.text_var,
            font=("Helvetica", 14, "bold"),
            bg=SOFT,
            fg=ACCENT_DARK,
            wraplength=480,
            justify="center",
            padx=12,
            pady=10,
        ).pack(fill="x")

        tk.Label(
            text_panel,
            text="Pritisni Shift za shranitev trenutno prepoznane črke",
            font=("Helvetica", 10),
            bg=CARD,
            fg=MUTED,
            wraplength=480,
            justify="center",
        ).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 4))

        btn_row = tk.Frame(text_panel, bg=CARD)
        btn_row.grid(row=2, column=0, columnspan=2, sticky="ew")
        btn_row.columnconfigure(0, weight=1)
        btn_row.columnconfigure(1, weight=1)
        self._style_button(btn_row, "Počisti besedilo", self.clear_text, 0, 0, width=18)
        self._style_button(btn_row, "Zbriši zadnjo črko", self.clear_previous_letter, 0, 1, width=18)

        self.right = tk.Frame(
            main,
            width=SIDEBAR_WIDTH,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self.right.grid(row=0, column=1, sticky="ns")
        self.right.grid_propagate(False)

        tk.Label(
            self.right,
            text="Prepoznava znaka",
            font=("Helvetica", 13, "bold"),
            bg=CARD,
            fg=INK,
        ).pack(pady=(14, 4), padx=12, anchor="w")

        self.lbl_var = tk.StringVar(value="Trenutni znak: A")
        tk.Label(
            self.right,
            textvariable=self.lbl_var,
            font=("Helvetica", 12),
            bg=CARD,
            fg=MUTED,
            wraplength=SIDEBAR_WIDTH - 24,
            justify="left",
        ).pack(pady=(0, 4), padx=14, anchor="w")

        self.pred_var = tk.StringVar(value="AI znak: —")
        tk.Label(
            self.right,
            textvariable=self.pred_var,
            font=("Helvetica", 20, "bold"),
            bg=CARD,
            fg=ACCENT_DARK,
            wraplength=SIDEBAR_WIDTH - 24,
            justify="left",
        ).pack(pady=(0, 8), padx=14, anchor="w")

        tk.Label(
            self.right,
            text="Črka A–Z · drži Enter za posnetek",
            font=("Helvetica", 10),
            bg=CARD,
            fg=MUTED,
            justify="left",
        ).pack(pady=(0, 8), padx=14, anchor="w")

        ttk.Separator(self.right, orient="horizontal").pack(fill="x", padx=14, pady=8)

        tk.Label(
            self.right,
            text="Samodejno naročilo s STM32",
            font=("Helvetica", 13, "bold"),
            bg=CARD,
            fg=INK,
        ).pack(pady=(4, 4), padx=14, anchor="w")

        stm32_row = tk.Frame(self.right, bg=CARD)
        stm32_row.pack(pady=(0, 4), padx=14, fill="x")
        self._fetch_btn = tk.Button(
            stm32_row,
            text="▶ Prenesi zadnjo & prepoznaj",
            command=self._on_fetch_stm32,
            bg=ACCENT,
            fg="white",
            activebackground=ACCENT_DARK,
            activeforeground="white",
            relief="flat",
            padx=8,
            pady=6,
            font=("Helvetica", 10, "bold"),
            cursor="hand2",
        )
        self._fetch_btn.pack(fill="x")

        self.stm32_var = tk.StringVar(value="Zahteva storitev na 127.0.0.1:5000")
        tk.Label(
            self.right,
            textvariable=self.stm32_var,
            font=("Helvetica", 10),
            bg=CARD,
            fg=MUTED,
            wraplength=SIDEBAR_WIDTH - 24,
            justify="left",
        ).pack(pady=(0, 8), padx=14, anchor="w")

        ttk.Separator(self.right, orient="horizontal").pack(fill="x", padx=14, pady=8)

        tk.Label(
            self.right,
            text="Govor v naročilo",
            font=("Helvetica", 13, "bold"),
            bg=CARD,
            fg=INK,
        ).pack(pady=(4, 4), padx=14, anchor="w")

        tk.Label(
            self.right,
            text="Izberi testni posnetek (testing_data/)",
            font=("Helvetica", 10),
            bg=CARD,
            fg=MUTED,
            justify="left",
        ).pack(pady=(0, 6), padx=14, anchor="w")

        list_frame = tk.Frame(self.right, bg=CARD)
        list_frame.pack(fill="x", padx=14, pady=(0, 8))

        scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        self.wav_list = tk.Listbox(
            list_frame,
            height=6,
            exportselection=False,
            activestyle="dotbox",
            yscrollcommand=scrollbar.set,
            bg="white",
            fg=INK,
            selectbackground=ACCENT,
            selectforeground="white",
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        scrollbar.config(command=self.wav_list.yview)
        self.wav_list.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.set_wav_files(wav_files)

        btn_row = tk.Frame(self.right, bg=CARD)
        btn_row.pack(pady=(0, 6), padx=14, anchor="w")
        self._style_button(btn_row, "Osveži", self._on_refresh, 0, 0)
        self._style_button(btn_row, "Predvajaj WAV", self._on_play_wav, 0, 1)

        action_row = tk.Frame(self.right, bg=CARD)
        action_row.pack(pady=(0, 8), padx=14, fill="x")
        self._style_button(action_row, "Prepoznaj naročilo", self._on_predict, 0, 0, colspan=2, width=28)
        self._style_button(
            action_row, "Predvajaj potrditev", self._on_play_signs, 1, 0, colspan=2, width=28
        )

        self.order_var = tk.StringVar(value="Vaše naročilo: še ni potrjeno.")
        order_box = tk.Frame(self.right, bg=SOFT, highlightbackground=BORDER, highlightthickness=1)
        order_box.pack(fill="x", padx=14, pady=(4, 12))
        tk.Label(
            order_box,
            textvariable=self.order_var,
            font=("Helvetica", 12, "bold"),
            bg=SOFT,
            fg=ACCENT_DARK,
            wraplength=SIDEBAR_WIDTH - 36,
            justify="left",
            padx=10,
            pady=10,
        ).pack(fill="x")

        self._style_button(self.right, "ZAPRI", self.destroy, pack=True, pady=(0, 14))

    def _build_footer(self, parent: tk.Frame) -> None:
        footer = tk.Label(
            parent,
            text="Oddaj naročilo z govornim posnetkom ali z znaki rok — sistem ga primerja z menijem zgoraj.",
            font=("Helvetica", 10),
            bg=BG,
            fg=MUTED,
            wraplength=1100,
            justify="center",
        )
        footer.pack(fill="x", pady=(8, 0))

    def _style_button(
        self,
        parent,
        text,
        command,
        row=None,
        column=None,
        colspan=1,
        width=12,
        pack=False,
        pady=0,
    ) -> None:
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            bg=ACCENT,
            fg="white",
            activebackground=ACCENT_DARK,
            activeforeground="white",
            relief="flat",
            padx=8,
            pady=6,
            font=("Helvetica", 10, "bold"),
            cursor="hand2",
        )
        if pack:
            btn.pack(pady=pady)
        else:
            btn.grid(row=row, column=column, columnspan=colspan, padx=3, pady=3, sticky="ew")

    def set_wav_files(self, wav_files: list[str]) -> None:
        self.wav_list.delete(0, tk.END)
        for name in wav_files:
            self.wav_list.insert(tk.END, name)
        if wav_files:
            self.wav_list.selection_set(0)
            self.wav_list.activate(0)
            self.wav_list.see(0)

    def set_highlighted_product(self, word: str | None) -> None:
        key = unicodedata.normalize("NFKD", (word or "")).encode("ascii", "ignore").decode("ascii").lower()
        for name, lbl in self._menu_labels.items():
            if key and (name in key or key in name):
                lbl.configure(bg=HIGHLIGHT, fg="white")
            else:
                lbl.configure(bg=CARD, fg=ACCENT_DARK)

    def set_lbl(self, lbl: str) -> None:
        if lbl:
            self.lbl_var.set(f"Trenutni znak: {lbl.upper()}")

    def set_prediction(self, label: str, confidence: float) -> None:
        pct = int(confidence * 100)
        self.pred_var.set(f"AI znak: {label}  ({pct}%)")

    def set_text(self, text: str) -> None:
        display = text.upper() if text else ""
        self.text_var.set(f"Trenutno besedilo: {display}" if display else "Trenutno besedilo:")

    def commit_letter(self, letter: str) -> bool:
        if not letter or letter in ("?", "—"):
            return False
        self._text.set(self._text.get() + letter)
        self.set_text(self._text.get())
        return True

    def clear_text(self) -> None:
        self._text.set("")
        self.set_text("")

    def clear_previous_letter(self) -> None:
        curr_text = self._text.get()
        if curr_text:
            self._text.set(curr_text[:-1])
            self.set_text(self._text.get())

    def set_audio_result(self, text: str) -> None:
        self.order_var.set(text if text.startswith("Vaše naročilo") else f"Vaše naročilo: {text}")

    def set_stm32_status(self, text: str) -> None:
        self.stm32_var.set(text)

    def set_stm32_busy(self, busy: bool) -> None:
        if self._fetch_btn is not None:
            self._fetch_btn.configure(state="disabled" if busy else "normal")

    def get_selected_wav(self) -> str:
        selection = self.wav_list.curselection()
        if not selection:
            return ""
        return str(self.wav_list.get(selection[0])).strip()

    def update_video(self, frame) -> None:
        self.video_panel.update(frame)

    def after(self, delay, callback) -> None:
        self.root.after(delay, callback)

    def set_close_callback(self, callback) -> None:
        self.root.protocol("WM_DELETE_WINDOW", callback)

    def start(self) -> None:
        self.root.mainloop()

    def destroy(self) -> None:
        self.root.destroy()
