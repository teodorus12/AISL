import mediapipe as mp
import cv2 as cv2

'''
    This class uses the landmarks found on ones hand and then imputs their location onto the hand if it exists.
'''

class LandMarkDrawer:
    vse_povezave = [
        (0,1),(1,2),(2,3),(3,4),
        (0,5),(5,6),(6,7),(7,8),
        (5,9),(9,10),(10,11),(11,12),
        (9,13),(13,14),(14,15),(15,16),
        (13,17),(17,18),(18,19),(19,20),
        (0,17)
    ]
    
    def draw(self, frame, rez):
        height, width, _ = frame.shape

        for hand_landmarks in rez.hand_landmarks:
            points = []
            
            for landmark in hand_landmarks:
                x = int(landmark.x * width)
                y = int(landmark.y * height)
                points.append((x, y))
                cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

            for povezave in self.vse_povezave:
                start_i, end_i = povezave
                cv2.line(frame, points[start_i], points[end_i], (255, 0, 0), 2)

        return frame