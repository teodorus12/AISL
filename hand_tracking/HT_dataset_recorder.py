import json
import time
import os

class DatasetRecorder:

    def __init__(self, out_dir="Handtracking/clips"):

        self.out_dir = out_dir
        self.rec = False
        self.curr_seq = []
        self.curr_lbl = "A"
        os.makedirs(self.out_dir, exist_ok=True)

    def start_recording(self, label):

        self.rec = True
        self.curr_seq = []
        self.curr_lbl = label
        print(f"[REC - HT] Started recording: {label}")
    
    def stop_recording(self):
        if not self.rec:
            return

        self.rec = False
        if len(self.curr_seq) == 0:
            print("[REC - HT] Empty sequence")
            return

        self.save_seq()
        self.curr_seq = []
        print("[REC - HT] Recording stopped")
        
    def add_frame_data(self, feature_data):
        if not self.rec:
            return

        frame_data = {
                    "timestamp": time.time(),
                    "feature_vector": feature_data["feature_vector"],
                    "normalized_landmarks": feature_data["normalized_landmarks"],
                    "bone_vectors": feature_data["normalized_vectors"]
        }
        self.curr_seq.append(frame_data)
        
    def save_seq(self):

        label_dir = os.path.join(self.out_dir, self.curr_lbl)
        os.makedirs(label_dir, exist_ok=True)
        timestamp = int(time.time() * 1000)

        filename = (f"{self.curr_lbl}_{timestamp}.json")
        filepath = os.path.join(label_dir, filename)

        sequence_data = {
                        "label": self.curr_lbl,
                        "sequence_length": len(self.curr_seq),
                        "frames": self.curr_seq
        }

        with open(filepath, "w") as f:
            json.dump(sequence_data, f, indent=4)

        print(f"[REC] Saved: {filepath}")