import cv2
from aruco_detect import ArucoDetector
from threading import Thread
from typing import Tuple, Optional

class Camera:
    def __init__(self, camera_index=0):
        self.cap=cv2.VideoCapture(camera_index)
        self.aruco_detector= ArucoDetector()
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self._stopped = False
        self._frame=None
        self._thread: Optional[Thread]= None

    def start(self):
        self._thread = Thread(target=self.update, daemon=True)
        self._thread.start()
        return self
    
    def update(self):
        while not self._stopped:
            ret, frame = self.cap.read()
            self._frame = frame

    def get_frame(self):
        return self._frame
    
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
        self._stopped = True
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self.cap.release()
        cv2.destroyAllWindows()
           
Cameraobj = Camera()
Cameraobj.start()
Cameraobj.detect_aruco()
