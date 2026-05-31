"""
HT_ai.py  —  Live Sign Language Recogniser
============================================
Drop this file into your hand_tracking/ folder.
It loads the trained model and runs live predictions.

In HT_hand_tracking.py, initialise it once:

    from hand_tracking.HT_ai import SignRecogniser
    self.recogniser = SignRecogniser()

Then inside update_loop(), after you have f_data, call:

    label, confidence = self.recogniser.predict(f_data)
    self.window.set_prediction(label, confidence)

And add set_prediction() to HT_window.py (see bottom of this file).
"""

import json
import os
import pickle
import numpy as np
from collections import deque

MODEL_PATH   = "models/sl_model.pkl"
CLASSES_PATH = "models/sl_classes.json"

# Smooth over this many consecutive frames to reduce flickering
SMOOTHING_FRAMES = 10
# Only show a prediction when confidence is above this threshold
CONFIDENCE_THRESHOLD = 0.6


class SignRecogniser:
    def __init__(self,
                 model_path: str = MODEL_PATH,
                 classes_path: str = CLASSES_PATH):

        self.model   = None
        self.classes = []
        self._history: deque = deque(maxlen=SMOOTHING_FRAMES)

        if not os.path.exists(model_path):
            print(f"[AI] Model not found at '{model_path}'. "
                  "Train it first with train_model.py")
            return

        with open(model_path, "rb") as f:
            self.model = pickle.load(f)

        with open(classes_path) as f:
            self.classes = json.load(f)

        print(f"[AI] Model loaded — classes: {self.classes}")

    def predict(self, feature_data: dict) -> tuple[str, float]:
        """
        Takes the dict returned by Serializer.vektor_processor() and
        returns (predicted_label, confidence).
        Returns ("?", 0.0) when no model is loaded or hand is not visible.
        """
        if self.model is None:
            return "?", 0.0

        vec = np.array(feature_data["feature_vector"], dtype=np.float32).reshape(1, -1)
        proba = self.model.predict_proba(vec)[0]
        best_idx = int(np.argmax(proba))
        confidence = float(proba[best_idx])

        if confidence < CONFIDENCE_THRESHOLD:
            self._history.append(None)
            return "?", confidence

        label = self.classes[best_idx]
        self._history.append(label)

        # Majority vote over the recent history window
        valid = [h for h in self._history if h is not None]
        if not valid:
            return "?", confidence

        smoothed = max(set(valid), key=valid.count)
        return smoothed, confidence

    def reset(self):
        """Call this when the hand disappears from frame."""
        self._history.clear()


# ─────────────────────────────────────────────────────────────────────────────
# HOW TO WIRE IT INTO HT_hand_tracking.py
# ─────────────────────────────────────────────────────────────────────────────
#
# 1.  Import at the top:
#         from hand_tracking.HT_ai import SignRecogniser
#
# 2.  In HandTrackingApp.__init__():
#         self.recogniser = SignRecogniser()
#
# 3.  Replace the relevant part of update_loop() with:
#
#         if detection_rez.hand_landmarks:
#             hand_landmarks = detection_rez.hand_landmarks[0]
#             f_data = self.serializer.vektor_processor(hand_landmarks)
#
#             # ── AI prediction ────────────────────────
#             label, conf = self.recogniser.predict(f_data)
#             self.window.set_prediction(label, conf)
#             # ─────────────────────────────────────────
#
#             self.recorder.add_frame_data(f_data)
#         else:
#             self.recogniser.reset()
#             self.window.set_prediction("—", 0.0)
#
# ─────────────────────────────────────────────────────────────────────────────
# ADD THIS METHOD to HT_window.py → MainWindow class:
# ─────────────────────────────────────────────────────────────────────────────
#
#     def set_prediction(self, label: str, confidence: float):
#         """Shows the live AI prediction in the right panel."""
#         pct = int(confidence * 100)
#         self.pred_var.set(f"AI: {label}  ({pct}%)")
#
# And add these two lines inside MainWindow.__init__(), in the right-panel block:
#
#         self.pred_var = tk.StringVar(value="AI: —")
#         tk.Label(self.right, textvariable=self.pred_var,
#                  font=("Helvetica", 28, "bold")).pack(pady=20)
#
# ─────────────────────────────────────────────────────────────────────────────