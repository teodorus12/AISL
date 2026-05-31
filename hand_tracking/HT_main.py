from hand_tracking.HT_hand_tracking import HandTrackingApp

'''
    this file acts as a startup for the hand tracking application
'''

def HT_startup():
    app = HandTrackingApp()
    app.start()
    
if __name__ == "__main__":
    HT_startup()