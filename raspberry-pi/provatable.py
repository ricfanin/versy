import time

import cv2
import numpy as np

from robot.camera import Camera
from vision.table_segmentation import TableSegmentor

camera = Camera()
camera.start()
segmentor = TableSegmentor()

start_time = time.time()
counter_frame = 0
count = 0

while True:
    frame = camera.get_frame()
    if frame is None:
        continue
    frame = frame.copy()
    counter_frame += 1

    mask = segmentor.detect(frame)

    overlay = frame.copy()
    overlay[mask > 0] = [0, 255, 0]
    result = cv2.addWeighted(frame, 0.6, overlay, 0.4, 0)

    table_pct = (mask > 0).mean() * 100
    cv2.putText(
        result,
        f"Table: {table_pct:.1f}%",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2,
    )
    cv2.imshow("Table Segmentation", result)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("p"):
        count += 1
        cv2.imwrite(f"frame_{count}.jpg", frame)
        cv2.imwrite(f"mask_{count}.png", mask)
        cv2.imwrite(f"result_{count}.jpg", result)
        print(f"Salvato: frame_{count}.jpg, mask_{count}.png, result_{count}.jpg")
    if key == ord("q"):
        camera.stop()
        cv2.destroyAllWindows()
        break

finish_time = time.time()
fps = counter_frame / (finish_time - start_time)
print(f"fps: {fps:.2f}")
