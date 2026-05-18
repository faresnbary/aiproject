# Hybrid Robotic System: Autonomous Tracking and Hand Gesture Control

## Project Overview

This project implements a hybrid robotic AI system that combines computer vision, deep learning inference, and robotic control.

The system supports two main operating modes:

1. **Hand Gesture Control Mode**  
   The robot receives movement commands based on real-time hand gesture recognition using MediaPipe.

2. **Object Tracking Mode**  
   The robot tracks a target object using YOLO object detection and generates movement commands according to the object’s position in the camera frame.

The final goal is to connect the AI system to an Arduino-based robotic car, where the generated commands are sent to the Arduino and translated into motor actions.

---

## Project Goal

The purpose of the project is to demonstrate the integration of pretrained neural network models in a robotic system.

The project does not train a neural network from scratch. Instead, it uses existing pretrained models for real-time inference:

- **MediaPipe Hands** for hand landmark detection and gesture recognition.
- **YOLOv8n** for real-time object detection and tracking.

---

## System Modes

### 1. Gesture Control Mode

In this mode, the camera detects the user’s hand and classifies the number of open fingers.

The detected gesture is converted into a robot command:

| Gesture | Command |
|---|---|
| 4 fingers open | FORWARD |
| 3 fingers open | BACKWARD |
| 2 fingers open | LEFT |
| 1 finger open | RIGHT |
| Fist / 0 fingers open | STOP |

The system also includes a stability mechanism, so a command is sent only after the same gesture is detected for several consecutive frames.

---

### 2. Object Tracking Mode

In this mode, YOLO detects objects from the camera feed.

The system selects a target object, calculates its center position, and compares it with the center of the camera frame.

| Object Position | Command |
|---|---|
| Object is left of center | LEFT |
| Object is right of center | RIGHT |
| Object is near the center | FORWARD |
| No object detected | STOP |

This creates a simple closed-loop behavior where visual feedback is used to adjust the robot’s movement.

---

## Command Mapping

Both modes generate the same movement commands:

| AI Command | Arduino Command |
|---|---|
| FORWARD | F |
| BACKWARD | B |
| LEFT | L |
| RIGHT | R |
| STOP | S |

This makes the system modular, because both Gesture Mode and Tracking Mode can control the same robot movement layer.

---

## Technologies Used

- Python
- OpenCV
- MediaPipe
- YOLOv8 / Ultralytics
- Arduino
- Serial Communication
- DC Motors
- Motor Driver
- HC-05 Bluetooth Module, optional for wireless communication

---

## Project Structure

```text
RobotAIProject/
├── arduino/
│   └── robot_car_control/
│       └── robot_car_control.ino
├── python/
│   ├── camera_test.py
│   ├── gesture_test.py
│   ├── gesture_control.py
│   ├── object_tracking.py
│   ├── object_tracking_stable.py
│   └── main_robot_ai.py
├── docs/
├── demo/
├── README.md
└── .gitignore