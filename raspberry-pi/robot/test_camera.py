import sys


from vision.aruco_detect import ArucoDetector

sys.path.append("/usr/lib/python3/dist-packages")

from typing import Optional, Tuple



import cv2

from picamera2 import Picamera2

resolution: Tuple[int, int] = (320, 240)

brightness: Optional[float] = 0.1

hflip: bool = False

vflip: bool = True



cam = Picamera2()



full_fov_mode = None

for mode in cam.sensor_modes:

    # Controlla se il crop_limits inizia da (0,0) - indica full FOV

    if mode["crop_limits"][0] == 0 and mode["crop_limits"][1] == 0:

        full_fov_mode = mode

        break



config = cam.create_video_configuration(

    main={"size": resolution, "format": "RGB888"},

    sensor={

        "output_size": full_fov_mode[

            "size"

        ],  # Forza il sensor mode con full FOV

        "bit_depth": full_fov_mode["bit_depth"],

    },

)



if hflip or vflip:

    from libcamera import Transform



    config["transform"] = Transform(hflip=int(hflip), vflip=int(vflip))



cam.configure(config)



if brightness is not None:

    cam.set_controls({"Brightness": float(brightness)})



cam.start()



frame_count = 0



while True:

    frame = cam.capture_array()
    aruco_detector = ArucoDetector()
    aruco_detector.detect(frame)

    # Modalità normale: mostra video ridimensionato

    # frame_small = cv2.resize(frame, (480, 360))

    cv2.imshow("Camera Test", frame)
    
    



    if cv2.waitKey(30) & 0xFF == ord("q"):

        break



cam.stop()

cv2.destroyAllWindows()