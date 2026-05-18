import cv2
from ultralytics import YOLO

# Load YOLO model
model = YOLO("yolov8n.pt")

# Open camera
cap = cv2.VideoCapture(0)

# Tracking settings
CENTER_TOLERANCE = 80
TARGET_CLASSES = ["person", "bottle", "cell phone", "cup"]

# Stability settings
last_sent_command = None
candidate_command = None
candidate_count = 0
STABLE_FRAMES_REQUIRED = 8


def decide_command(object_center_x, frame_center_x):
    """
    Decide robot movement according to object location in the frame.
    """
    error = object_center_x - frame_center_x

    if error < -CENTER_TOLERANCE:
        return "LEFT"
    elif error > CENTER_TOLERANCE:
        return "RIGHT"
    else:
        return "FORWARD"


def send_command(command):
    """
    For now, this prints the stable command.
    Later we will connect it to Arduino Serial.
    """
    print(f"Stable tracking command: {command}")


if not cap.isOpened():
    print("Camera not found")
    exit()


while True:
    ret, frame = cap.read()

    if not ret:
        print("Failed to read from camera")
        break

    frame = cv2.flip(frame, 1)

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

        command = decide_command(object_center_x, frame_center_x)

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

    # Stability logic
    if command == candidate_command:
        candidate_count += 1
    else:
        candidate_command = command
        candidate_count = 1

    if candidate_count >= STABLE_FRAMES_REQUIRED:
        if candidate_command != last_sent_command:
            send_command(candidate_command)
            last_sent_command = candidate_command

    # Draw center and tolerance lines
    cv2.line(frame, (frame_center_x, 0), (frame_center_x, height), (255, 0, 0), 2)
    cv2.line(frame, (frame_center_x - CENTER_TOLERANCE, 0), (frame_center_x - CENTER_TOLERANCE, height), (255, 255, 0), 1)
    cv2.line(frame, (frame_center_x + CENTER_TOLERANCE, 0), (frame_center_x + CENTER_TOLERANCE, height), (255, 255, 0), 1)

    cv2.putText(
        frame,
        f"Tracking Command: {command}",
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 255),
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

    cv2.imshow("Stable Object Tracking YOLO", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()