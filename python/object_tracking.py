import cv2
from ultralytics import YOLO

# Load YOLO model
# The first run may download the model automatically
model = YOLO("yolov8n.pt")

# Open camera
cap = cv2.VideoCapture(0)

# Frame zones
CENTER_TOLERANCE = 80

# Only track these classes for now
TARGET_CLASSES = ["person", "bottle", "cell phone", "cup"]


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

    # Run YOLO on current frame
    results = model(frame, verbose=False)

    command = "STOP"
    best_object = None
    best_confidence = 0

    # Go over detected objects
    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            class_name = model.names[class_id]
            confidence = float(box.conf[0])

            if class_name in TARGET_CLASSES and confidence > best_confidence:
                best_confidence = confidence
                best_object = box

    if best_object is not None:
        x1, y1, x2, y2 = best_object.xyxy[0]
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

        object_center_x = (x1 + x2) // 2
        object_center_y = (y1 + y2) // 2

        command = decide_command(object_center_x, frame_center_x)

        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Draw object center
        cv2.circle(frame, (object_center_x, object_center_y), 6, (0, 0, 255), -1)

        label = f"Target: {command} ({best_confidence:.2f})"
        cv2.putText(
            frame,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

    # Draw center line
    cv2.line(
        frame,
        (frame_center_x, 0),
        (frame_center_x, height),
        (255, 0, 0),
        2
    )

    # Draw left/right tolerance lines
    cv2.line(
        frame,
        (frame_center_x - CENTER_TOLERANCE, 0),
        (frame_center_x - CENTER_TOLERANCE, height),
        (255, 255, 0),
        1
    )

    cv2.line(
        frame,
        (frame_center_x + CENTER_TOLERANCE, 0),
        (frame_center_x + CENTER_TOLERANCE, height),
        (255, 255, 0),
        1
    )

    cv2.putText(
        frame,
        f"Tracking Command: {command}",
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 255),
        2
    )

    cv2.imshow("Object Tracking YOLO", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()