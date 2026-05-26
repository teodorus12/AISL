from hand_tracking.HT_camera_handler import CameraHandler
from hand_tracking.HT_handler import HandTracker
from hand_tracking.HT_landmark_drawer import LandMarkDrawer
from hand_tracking.HT_frame_handler import FrameProcessor
from hand_tracking.HT_serializer import Serializer
from hand_tracking.HT_dataset_recorder import DatasetRecorder
from hand_tracking.HT_window import MainWindow

'''
    This class handles the different aspects of communication between camera and then getting the cameras feed and then finally processing the correct image.
'''


class HandTrackingApp:
    def __init__(self):
        self.camera_handler = CameraHandler()
        self.hand_tracker = HandTracker()
        self.landmark_drawer = LandMarkDrawer()

        self.frame_processor = FrameProcessor(self.hand_tracker, self.landmark_drawer)
        self.window = MainWindow()
        self.serializer = Serializer()
        self.recorder = DatasetRecorder()
        self.current_label = "A"
        
        self.running = False
        self.setup_keybinds()
        
    def setup_keybinds(self):

        self.window.root.bind("<KeyPress>", self.on_key_press)
        self.window.root.bind("<KeyRelease-space>", self.on_space_release)
        
    def on_key_press(self, event):
        key = event.keysym.upper()

        if key == "SPACE":
            if not self.recorder.rec:
                self.recorder.start_recording(self.current_label)
            return

        if len(key) == 1 and key.isalpha():
            self.current_label = key
            print(f"[LABEL - HT] Current label: "f"{self.current_label}")

    def on_space_release(self, event):
        self.recorder.stop_recording()
        
    def start(self):
        self.camera_handler.open_camera()
        self.running = True
        
        self.landmark_serializer = Serializer()
        self.recorder = DatasetRecorder()
        self.current_label = "A"
        
        self.window.set_close_callback(self.stop)
        self.update_loop()
        self.window.start()

    def update_loop(self):
        if not self.running:
            return

        succ, frame = self.camera_handler.read_frame()

        
        if succ:
            processed_frame = self.frame_processor.process(frame)
            detection_rez = (self.hand_tracker.process(frame))
            
            if detection_rez.hand_landmarks:
                hand_landmarks = detection_rez.hand_landmarks[0]
                f_data = self.serializer.vektor_processor(hand_landmarks)
                
                self.recorder.add_frame_data(f_data)
                
            self.window.update_video(processed_frame)
            
            
        self.window.after(10, self.update_loop)

    def stop(self):
        self.running = False

        self.camera_handler.release_camera()
        self.hand_tracker.close()
        self.window.destroy()