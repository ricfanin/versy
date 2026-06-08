# Versy - Versatile Robot System

Versy is a robotic system featuring an omnidirectional mobile base (3 motors) and a liquid pump (1 motor), controlled by an MSP432 microcontroller and a Raspberry Pi. The system includes an Android companion app for remote manual operation (Joystick) and autonomous tasks (Pouring based on computer vision, Aruco markers, and YOLO segmentation).

---

## 1. Hardware and Software Requirements

### Hardware

* **MSP432P401R LaunchPad**: Real-time microcontroller for PWM generation.<br>
    <img src="images/msp432.png" alt="MSP432" width="250">

* **Motor Drivers**: 2x MC33926 drivers for motors and pump.<br>
    <img src="images/driver.png" alt="Motor Drivers" width="250">

* **Motors**: 3x DC motors for omni-wheels (kiwi-drive) + 1 DC pump.<br>
    <img src="images/motor_dc.png" alt="DC Motors" width="250"> <img src="images/pump.png" alt="DC Pump" width="250">

* **ToF**: 1 frontal ToF vl53l0x, calibrate the correct distance between robot and glass.<br>
    <img src="images/ToF.png" alt="ToF Sensor" width="250">

* **Raspberry Pi 4 (with Camera Module)**: Main computation unit, computer vision, and I2C master.<br>
    <img src="images/raspberrypi4.png" alt="Raspberry Pi 4" width="250">

* **Android Device**: Smartphone or tablet to run the companion app.<br>
    
* **Chessboard**: A 9x6 inner-corners chessboard (27mm squares) for camera calibration.<br>
    
### Software
*   **Code Composer Studio (CCS)**: To build and flash the MSP432 C firmware.
*   **Python 3.x**: On Raspberry Pi (FastAPI, WebSockets, OpenCV, Picamera2, ONNXRuntime).
*   **Android Studio**: To build the Kotlin/Jetpack Compose Android app.
*   **Ultralytics (YOLOv8)**: For training the computer vision segmentation models.

---

## 2. Project Layout (Source Code Organization)

Here is a breakdown of the most important files driving the logic in each directory:

```text
.
├── msp_432401r/
│   ├── main.c                                # Main I2C logic and loop
│   └── motor_driver/
│       ├── mc33926_driver.c                  # Low-level driver for the MC33926 (PWM, pins)
│       └── motor_driver.h                    # Header file for the motor driver
│ 
├── raspberry-pi/
│   ├── main.py                               # FastAPI/WebSocket server entry point
│   ├── config/
│   │   └── camera_calibration.py             # Script to run camera calibration
│   ├── machine/
│   │   ├── state_machine.py                  # Core state machine logic (handles transitions)
│   │   └── states/
│   │       ├── init_state.py                 # Initial phase
│   │       ├── scan_state.py                 # Searches for Aruco markers
│   │       ├── moving_state.py               # Approaches the marker
│   │       ├── pouring_state.py              # Vision-based segmentation to pour liquid
│   │       └── retreat_state.py              # Robot returns to home position
│   ├── robot/
│   │   ├── motors.py                         # I2C driver to communicate with the MSP432
│   │   └── camera.py                         # Picamera2 / OpenCV handler
│   ├── vision/
│   │   ├── aruco_detect.py                   # ArUco marker pose estimation and tracking
│   │   └── table_segmentation.py             # YOLOv8 inference for table/cup segmentation
│   └── websocket/
│       ├── server.py                         # WS connections management
│       └── handlers/
│           ├── action_handler.py             # Parses App commands (e.g. move joystick)
│           └── aruco_handler.py              # Streams detected markers back to the App
│           └── router.py                     # Routes messages to the correct handler 
│
├── versy_app/                                # Android Application
│   └── app/src/main/java/com/example/versy_app/
│       ├── MainActivity.kt
│       ├── viewmodel/AppViewModel.kt         # MVVM ViewModel to handle WebSocket and Robot state
│       ├── ui/screens/
│       │   ├── JoystickScreen.kt             # Manual control UI 
│       │   └── PourScreen.kt                 # Autonomous pouring UI (shows camera feed/markers)
│       └── data/
│           ├── RobotSocket.kt                # Socket connection handling in Android
│           └── Messages.kt                   # JSON serializers/deserializers for WS messages
│
└── segmentation/
    ├── datasets/yolo_dataset/data.yaml       # Dataset mapping for YOLO
    ├── training/
    │   └── train_yolov8_seg.py               # Script used to train YOLOv8 locally
    └── inference.py                          # Tests YOLOv8 model inference
```

---

## 3. How to Build, Burn, Run Project

### A. MSP432 Firmware
1. Open **Code Composer Studio**.
2. Import the `msp_432401r` project into your workspace.
3. Build the project (`Project -> Build Project`).
4. Connect the MSP432 LaunchPad via USB and click the **Debug** (or Flash) icon to burn the firmware.

### B. Raspberry Pi Backend & Camera Calibration
1. Connect to the Raspberry Pi and navigate to the `raspberry-pi` folder.
2. Install picamera2 required libraries:
   ```bash
   sudo apt install python3-libcamera python3-kms-cxx python3-picamera2
   ```
3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
4. **Camera Calibration**: Before using vision features, run the calibration script:
   ```bash
   python config/camera_calibration.py
   ```
   * Choose option **1** to capture images. Hold a printed chessboard in front of the camera and press `SPACE` when the corners are highlighted in green (capture ~20 images). Press `ESC` when done. You can use the following photo:
     <img src="images/chessboard.jpeg" alt="chessboard" width="250">
   * Choose option **2** to perform the calibration. This will generate a `camera_calibration.npz` file containing the camera matrix and distortion coefficients.
5. Start the main server:
   ```bash
   python main.py
   ```

### C. Android App (Versy App)
1. Open the `versy_app` folder in **Android Studio**.
2. Wait for Gradle synchronization.
3. Connect your Android device (ensure Developer Options and USB Debugging are enabled).
4. Click **Run 'app'** to build and install the APK on your device.

### D. YOLO Segmentation (Optional - Retraining)
1. Navigate to the `segmentation` folder.
2. Ensure you have PyTorch and Ultralytics installed.
3. Run `python training/train_yolov8_seg.py` to retrain the model on the provided dataset.

---

## 4. User Guide

1. **Power Up**: Turn on the robot base. Ensure both the MSP432 and the Raspberry Pi boot up and the FastAPI server is running.
2. **Connect**: Open the Versy app on your Android device. Go to the Settings panel and insert the IP address of the Raspberry Pi.
3. **Manual Control**: Navigate to the Joystick Screen to manually control the omni-wheels and test the movement.
4. **Autonomous Mode**: Place your glass on the personalized Versy coaster. Switch to the Pour Screen to begin the autonomous sequence, where the robot will approach the target (using Aruco and YOLO segmentation) and trigger the pump.

---

## 5. Media Links
*   **Slides Presentation**: [Link](https://canva.link/gac6j1pceaj32lf)
*   **YouTube Video**:  [Versy-Video](https://youtu.be/0izqmVGTUHI?si=aVkfisXJMKIOZBLL)

---

## 6. Team Members & Contributions
*   **Daniele Dalla Vecchia**: Camera Calibration, ArUco code detector, kiwi-drive kinematic, MSP432 firmware, I2C communication.
*   **Francesco Fanton**: State Machine logic, Fusion design, 3d printings and software tester and integrator.
*   **Mattia Tognato**: [Descrizione di cosa ha fatto Mattia, es. addestramento rete YOLO, script di segmentazione...]
*   **Riccardo Fanin**: [Descrizione di cosa ha fatto Riccardo, es. backend Raspberry Pi, WebSockets, calibrazione camera...]
