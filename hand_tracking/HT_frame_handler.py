import cv2

class FrameProcessor:
    def __init__(self, hand_tracker, landmarks):
        self.hand_tracker = hand_tracker
        self.landmarks = landmarks

    def process(self, frame):
        frame = cv2.flip(frame, 1)
        rez = self.hand_tracker.process(frame)
        frame = self.landmarks.draw(frame, rez)

        return frame