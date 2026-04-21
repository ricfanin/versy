import cv2
import time

from robot.camera import Camera

start_time = time.time()
counter_frame = 0
count = 0
camera = Camera()
camera.start()

while True:
    counter_frame += 1
    frame = camera.get_frame()
    if frame is None:
        continue
    frame = frame.copy()
    cv2.imshow("Frame", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("p"):
        count += 1
        cv2.imwrite(str(count) + ".jpg", frame)

    if key == ord("q"):
        camera.stop()
        cv2.destroyAllWindows()
        break

finish_time = time.time()
fps = counter_frame / (finish_time - start_time)
print("fps: ", fps)
