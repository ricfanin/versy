import cv2
import cv2.aruco as aruco
import math

def get_position(frame, corner):
    height, width = frame.shape[:2]
    center_x = width // 2
    center_y = height // 2
    for marker_corners in corner:
        points = marker_corners[0]
        marker_x = int(points[:,0].mean()) #[x0,x1,x2,x3]
        marker_y = int(points[:,1].mean()) #[y0,y1,y2,y3]
        dx= marker_x-center_x
        dy= marker_y -center_y
        distance = math.sqrt(dx**2 + dy**2)
    return (dx,dy,distance)


cap = cv2.VideoCapture(0)
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters= aruco.DetectorParameters() 
aruco_detector= aruco.ArucoDetector(aruco_dict, parameters)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    corners, ids, rejected = aruco_detector.detectMarkers(gray)

    # Se trova marker, disegna bordi e ID, e calcolo dist
    if ids is not None:
        aruco.drawDetectedMarkers(frame, corners, ids)
        (dx,dy,distance)= get_position(frame,corners)
        print(f"Distanza dal centro: x : {dx} , y : {dy} , distance:{distance}")
    
    cv2.imshow("ArUco Detection", frame)

    # Esco premendo 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()