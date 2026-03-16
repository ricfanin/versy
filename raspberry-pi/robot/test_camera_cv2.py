import cv2

cap = cv2.VideoCapture(0)

# Ottimizzazioni per performance
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break
    # Modalità normale: mostra video ridimensionato
    frame_small = cv2.resize(frame, (480, 360))
    cv2.imshow("Camera Test", frame_small)

    if cv2.waitKey(30) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
