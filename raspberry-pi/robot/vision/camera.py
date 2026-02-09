import cv2
from aruco_detect import ArucoDetector

class Camera:
    def __init__(self, camera_index=0):
        self.cap=cv2.VideoCapture(camera_index)
        self.aruco_detector= ArucoDetector()
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

    def get_frame(self):
        ret, frame = self.cap.read()
        return frame
    
    def detect_aruco(self):
        print("Premi 'q' per uscire dalla detection")
        while True:
            # FIX 1: Aggiungi le parentesi () per chiamare il metodo e ottenere il frame
            frame = self.get_frame()
            
            if frame is not None:
                self.aruco_detector.detect(frame)
            
            # FIX 2: waitKey è OBBLIGATORIO per aggiornare la finestra cv2.imshow
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.stop()
    
    def stop(self):
        self.cap.release()
        cv2.destroyAllWindows()
           
Cameraobj = Camera()
Cameraobj.detect_aruco()
