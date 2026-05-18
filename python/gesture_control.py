import cv2
import mediapipe as mp
import serial
import time

# =========================
# Serial / Arduino Settings
# =========================

USE_ARDUINO = False  # כרגע False כי עדיין לא חייבים Arduino מחובר
ARDUINO_PORT = "/dev/cu.usbmodem1101"  # נשנה אחר כך לפי הפורט האמיתי
BAUD_RATE = 9600

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

cap = cv2.VideoCapture(0)

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)


# =========================
# Command Settings
# =========================

COMMAND_MAP = {
    "FORWARD": "F",
    "BACKWARD": "B",
    "LEFT": "L",
    "RIGHT": "R",
    "STOP": "S"
}

last_sent_command = None
candidate_command = None
candidate_count = 0
STABLE_FRAMES_REQUIRED = 10


def is_finger_open(tip_y, pip_y):
    """
    Checks if a finger is open.
    In image coordinates, smaller y means the point is higher.
    """
    return tip_y < pip_y


def detect_gesture(hand_landmarks):
    """
    Detects hand gestures and converts them into robot movement commands.
    Thumb is ignored for better stability.
    """

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


def send_command(command):
    """
    Sends command to Arduino if enabled.
    Otherwise, prints it as simulation.
    """

    short_command = COMMAND_MAP.get(command)

    if short_command is None:
        return

    if USE_ARDUINO and arduino is not None:
        arduino.write(short_command.encode())
        print(f"Sent to Arduino: {command} -> {short_command}")
    else:
        print(f"Simulation command: {command} -> {short_command}")


if not cap.isOpened():
    print("Camera not found")
    exit()


# =========================
# Main Loop
# =========================

while True:
    ret, frame = cap.read()

    if not ret:
        print("Failed to read from camera")
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb_frame)

    gesture = "No Hand"

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            gesture = detect_gesture(hand_landmarks)

    # Stability logic
    if gesture in ["No Hand", "UNKNOWN"]:
        candidate_command = None
        candidate_count = 0
    else:
        if gesture == candidate_command:
            candidate_count += 1
        else:
            candidate_command = gesture
            candidate_count = 1

        if candidate_count >= STABLE_FRAMES_REQUIRED:
            if candidate_command != last_sent_command:
                send_command(candidate_command)
                last_sent_command = candidate_command

    cv2.putText(
        frame,
        f"Gesture: {gesture}",
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame,
        f"Stable: {candidate_command} ({candidate_count}/{STABLE_FRAMES_REQUIRED})",
        (30, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Last Sent: {last_sent_command}",
        (30, 130),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 0),
        2
    )

    mode_text = "Mode: Simulation" if not USE_ARDUINO else "Mode: Arduino"
    cv2.putText(
        frame,
        mode_text,
        (30, 170),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    cv2.imshow("Robot Gesture Control", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
hands.close()

if arduino is not None:
    arduino.close()

cv2.destroyAllWindows()