import cv2
import mediapipe as mp

# MediaPipe setup
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

# Open camera
cap = cv2.VideoCapture(0)

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)


def is_finger_open(tip_y, pip_y):
    """
    Checks if a finger is open.
    In image coordinates, smaller y means the point is higher.
    """
    return tip_y < pip_y


def detect_gesture(hand_landmarks):
    """
    Detects hand gestures and converts them into robot commands.
    This version ignores the thumb because thumb detection is less stable.
    """

    landmarks = hand_landmarks.landmark

    # Index finger
    index_tip = landmarks[8]
    index_pip = landmarks[6]

    # Middle finger
    middle_tip = landmarks[12]
    middle_pip = landmarks[10]

    # Ring finger
    ring_tip = landmarks[16]
    ring_pip = landmarks[14]

    # Pinky finger
    pinky_tip = landmarks[20]
    pinky_pip = landmarks[18]

    # Check which fingers are open
    index_open = is_finger_open(index_tip.y, index_pip.y)
    middle_open = is_finger_open(middle_tip.y, middle_pip.y)
    ring_open = is_finger_open(ring_tip.y, ring_pip.y)
    pinky_open = is_finger_open(pinky_tip.y, pinky_pip.y)

    open_count = sum([
        index_open,
        middle_open,
        ring_open,
        pinky_open
    ])

    # Gesture mapping
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


if not cap.isOpened():
    print("Camera not found")
    exit()


while True:
    ret, frame = cap.read()

    if not ret:
        print("Failed to read from camera")
        break

    # Mirror the image for easier control
    frame = cv2.flip(frame, 1)

    # Convert BGR image to RGB for MediaPipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb_frame)

    gesture = "No Hand"

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:

            # Draw hand landmarks
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            # Detect gesture
            gesture = detect_gesture(hand_landmarks)

    # Show gesture on screen
    cv2.putText(
        frame,
        f"Gesture: {gesture}",
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    # Show window
    cv2.imshow("Gesture Control Test", frame)

    # Press q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
hands.close()
cv2.destroyAllWindows()
