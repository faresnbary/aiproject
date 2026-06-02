import cv2
import mediapipe as mp
from ultralytics import YOLO
import serial
import time

# =========================
# General Settings
# =========================

USE_ARDUINO = True
ARDUINO_PORT = "/dev/cu.usbserial-A5069RR4"
BAUD_RATE = 9600

STABLE_FRAMES_REQUIRED = 8

COMMAND_MAP = {
    "FORWARD": "F",
    "BACKWARD": "B",
    "LEFT": "L",
    "RIGHT": "R",
    "STOP": "S"
}

arduino = None

if USE_ARDUINO:
    try:
        arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        print("Connected to Arduino")
    except Exception as e:
        print(f"Could not connect to Arduino: {e}")
        arduino = None

# =========================
# MediaPipe Setup
# =========================

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# =========================
# YOLO Setup
# =========================

model = YOLO("yolov8n.pt")

TARGET_CLASSES = ["person", "bottle", "cell phone", "cup"]
CENTER_TOLERANCE = 80

# =========================
# Camera Setup
# =========================

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera not found")
    exit()

# =========================
# Stability Variables
# =========================

current_mode = "GESTURE"

last_sent_command = None
candidate_command = None
candidate_count = 0


# =========================
# Helper Functions
# =========================

def reset_stability():
    global last_sent_command, candidate_command, candidate_count
    last_sent_command = None
    candidate_command = None
    candidate_count = 0


def is_finger_open(tip_y, pip_y):
    return tip_y < pip_y


def detect_gesture(hand_landmarks):
    landmarks = hand_landmarks.landmark

    index_open = is_finger_open(landmarks[8].y, landmarks[6].y)
    middle_open = is_finger_open(landmarks[12].y, landmarks[10].y)
    ring_open = is_finger_open(landmarks[16].y, landmarks[14].y)
    pinky_open = is_finger_open(landmarks[20].y, landmarks[18].y)

    open_count = sum([
        index_open,
        middle_open,
        ring_open,
        pinky_open
    ])

    if open_count == 4:
        return "FORWARD"
    elif open_count == 3:
        return "BACKWARD"
    elif open_count == 2:
        return "LEFT"
    elif open_count == 1:
        return "RIGHT"
    elif open_count == 0:
        return "STOP"
    else:
        return "UNKNOWN"


def process_gesture_mode(frame):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    command = "No Hand"

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )
            command = detect_gesture(hand_landmarks)

    return frame, command


def decide_tracking_command(object_center_x, frame_center_x):
    error = object_center_x - frame_center_x

    if error < -CENTER_TOLERANCE:
        return "LEFT"
    elif error > CENTER_TOLERANCE:
        return "RIGHT"
    else:
        return "FORWARD"


def process_tracking_mode(frame):
    height, width, _ = frame.shape
    frame_center_x = width // 2

    results = model(frame, verbose=False)

    command = "STOP"
    best_object = None
    best_confidence = 0
    best_class_name = ""

    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            class_name = model.names[class_id]
            confidence = float(box.conf[0])

            if class_name in TARGET_CLASSES and confidence > best_confidence:
                best_confidence = confidence
                best_object = box
                best_class_name = class_name

    if best_object is not None:
        x1, y1, x2, y2 = best_object.xyxy[0]
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

        object_center_x = (x1 + x2) // 2
        object_center_y = (y1 + y2) // 2

        command = decide_tracking_command(object_center_x, frame_center_x)

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.circle(frame, (object_center_x, object_center_y), 6, (0, 0, 255), -1)

        label = f"{best_class_name}: {best_confidence:.2f}"
        cv2.putText(
            frame,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

    cv2.line(frame, (frame_center_x, 0), (frame_center_x, height), (255, 0, 0), 2)
    cv2.line(frame, (frame_center_x - CENTER_TOLERANCE, 0), (frame_center_x - CENTER_TOLERANCE, height), (255, 255, 0), 1)
    cv2.line(frame, (frame_center_x + CENTER_TOLERANCE, 0), (frame_center_x + CENTER_TOLERANCE, height), (255, 255, 0), 1)

    return frame, command


def send_command(command):
    short_command = COMMAND_MAP.get(command)

    if short_command is None:
        return

    if USE_ARDUINO and arduino is not None:
        arduino.write(short_command.encode())
        print(f"Sent to Arduino: {command} -> {short_command}")
    else:
        print(f"Simulation command: {command} -> {short_command}")


def update_stable_command(command):
    global last_sent_command, candidate_command, candidate_count

    if command in ["No Hand", "UNKNOWN"]:
        candidate_command = None
        candidate_count = 0
        return

    if command == candidate_command:
        candidate_count += 1
    else:
        candidate_command = command
        candidate_count = 1

    if candidate_count >= STABLE_FRAMES_REQUIRED:
        if candidate_command != last_sent_command:
            send_command(candidate_command)
            last_sent_command = candidate_command


def draw_interface(frame, command):
    cv2.putText(
        frame,
        f"Mode: {current_mode}",
        (30, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Command: {command}",
        (30, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Stable: {candidate_command} ({candidate_count}/{STABLE_FRAMES_REQUIRED})",
        (30, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Last Sent: {last_sent_command}",
        (30, 155),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 0),
        2
    )

    status = "Arduino Connected" if arduino is not None else "Arduino Not Connected"
    cv2.putText(
        frame,
        status,
        (30, 190),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0) if arduino is not None else (0, 0, 255),
        2
    )

    cv2.putText(
        frame,
        "Press G = Gesture | T = Tracking | Q = Quit",
        (30, frame.shape[0] - 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    return frame


# =========================
# Main Loop
# =========================

print("Robot AI System Started")
print("Press G for Gesture Mode")
print("Press T for Tracking Mode")
print("Press Q to Quit")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Failed to read from camera")
        break

    frame = cv2.flip(frame, 1)

    if current_mode == "GESTURE":
        frame, command = process_gesture_mode(frame)
    elif current_mode == "TRACKING":
        frame, command = process_tracking_mode(frame)
    else:
        command = "STOP"

    update_stable_command(command)
    frame = draw_interface(frame, command)

    cv2.imshow("Hybrid Robot AI System", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        send_command("STOP")
        break

    elif key == ord("g"):
        current_mode = "GESTURE"
        reset_stability()
        send_command("STOP")
        print("Switched to Gesture Mode")

    elif key == ord("t"):
        current_mode = "TRACKING"
        reset_stability()
        send_command("STOP")
        print("Switched to Tracking Mode")


cap.release()
hands.close()

if arduino is not None:
    send_command("STOP")
    arduino.close()

cv2.destroyAllWindows()