import cv2
import platform as pf

'''
    This class opens, reads and releases camera footage.
'''

class CameraHandler:
    def __init__(self, camera_i=0):
        self.camera_i = camera_i
        self.cap = None

    def open_camera(self):
        os = pf.system()
        if os == 'Darwin':
            self.cap = cv2.VideoCapture(self.camera_i, cv2.CAP_AVFOUNDATION)
        else:
            self.cap = cv2.VideoCapture(self.camera_i)
            

        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera")

    def read_frame(self):
        if self.cap is None:
            return False, None

        return self.cap.read()

    def release_camera(self):
        if self.cap:
            self.cap.release()