from hand_tracking.HT_camera_handler import CameraHandler
from hand_tracking.HT_handler import HandTracker
from hand_tracking.HT_landmark_drawer import LandMarkDrawer
from hand_tracking.HT_frame_handler import FrameProcessor

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
        self.running = False

    def start(self):
        self.camera_handler.open_camera()
        self.running = True

        self.window.set_close_callback(self.stop)
        self.update_loop()
        self.window.start()

    def update_loop(self):
        if not self.running:
            return

        succ, frame = self.camera_handler.read_frame()

        if succ:
            processed_frame = self.frame_processor.process(frame)
            self.window.update_video(processed_frame)
        self.window.after(10, self.update_loop)

    def stop(self):
        self.running = False

        self.camera_handler.release_camera()
        self.hand_tracker.close()
        self.window.destroy()