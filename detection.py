# detection.py
import cv2
import numpy as np
import tensorflow as tf
from ultralytics import YOLO
from collections import defaultdict
from config import YOLO_MODEL_PATH, CLF_MODEL_PATH, TYPE_MODEL_PATH, CLASSES, DISEASE_CLASSES

# Load Models
yolo_model = YOLO(YOLO_MODEL_PATH)
clf_model = tf.keras.models.load_model(CLF_MODEL_PATH)
clf_type_model = tf.keras.models.load_model(TYPE_MODEL_PATH)

def get_green_mask(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_green = np.array([35, 40, 40])
    upper_green = np.array([85, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)

    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel)
    return mask

def predict_video(path=None):
    if path is None:
        print("Please provide a video path.")
        return

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print("Error opening video")
        return

    track_history = defaultdict(list)
    track_history_type = defaultdict(list)
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        frame = cv2.resize(frame, (640, 480))
        results = yolo_model.track(frame, persist=True, conf=0.25, verbose=False)

        for r in results:
            if r.boxes is None:
                continue

            boxes = r.boxes.xyxy.cpu().numpy()
            ids = r.boxes.id.cpu().numpy() if r.boxes.id is not None else np.arange(len(boxes))

            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = map(int, box)
                track_id = int(ids[i])

                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)

                h = y2 - y1
                leaf_crop = frame[y1:int(y1 + 0.6*h), x1:x2]
                full_img = frame[y1:y2, x1:x2]
                
                if leaf_crop.size == 0:
                    continue

                mask = get_green_mask(leaf_crop)
                leaf_only = cv2.bitwise_and(leaf_crop, leaf_crop, mask=mask)

                if leaf_only.size == 0:
                    continue

                if frame_count % 5 == 0:
                    try:
                        input_img = cv2.resize(full_img, (224, 224))
                        input_img = np.expand_dims(input_img, axis=0)

                        pred = clf_model.predict(input_img, verbose=0)[0]
                        track_history[track_id].append(pred)

                        if len(track_history[track_id]) > 10:
                            track_history[track_id].pop(0)
                    except:
                        continue

                if len(track_history[track_id]) > 0:
                    avg_pred = np.mean(track_history[track_id], axis=0)
                    label = CLASSES[np.argmax(avg_pred)]
                    confidence = np.max(avg_pred)
                else:
                    label = "Detecting..."
                    confidence = 0

                disease_label = ""
                if label not in ["Healthy", "Detecting...", "healthy"]:
                    try:
                        disease_pred = clf_type_model.predict(input_img, verbose=0)[0]
                        disease_label = DISEASE_CLASSES[np.argmax(disease_pred)]
                        track_history_type[track_id].append(disease_pred)
                    except:
                        disease_label = "Unknown"

                color = (0, 255, 0) if label.lower() == "healthy" else (0, 0, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)

                text = f"ID {track_id} | {label}"
                if disease_label != "":
                    text += f" ({disease_label})"
                text += f" {confidence:.2f}"

                y_text = max(40, y1)
                cv2.rectangle(frame, (x1, y_text-30), (x1+300, y_text), color, -1)
                cv2.putText(frame, text, (x1+5, y_text-8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.imshow("Palm Detection", frame)
        if cv2.waitKey(20) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    return track_history, track_history_type

# detection.py (Add this to the bottom of the file)
import os

def predict_image(image_path, output_path="output_result.jpg"):
    """
    Detects diseases in a single image, saves the annotated image, 
    and returns formatted results for the RAG report generator.
    """
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Image not found at {image_path}")
        return None

    img = cv2.resize(img, (640, 640))
    results = yolo_model.track(img, persist=True, conf=0.25, verbose=False)
    frame = img.copy()
    
    # Dictionary to hold results for the RAG report generator
    tree_results = {}
    tree_counter = 1

    for r in results:
        if r.boxes is None:
            continue

        boxes = r.boxes.xyxy.cpu().numpy()

        for box in boxes:
            x1, y1, x2, y2 = map(int, box)
            h = y2 - y1
            leaf_crop = frame[y1:y2, x1:x2]

            if leaf_crop.size == 0:
                continue

            input_img = cv2.resize(leaf_crop, (224, 224))
            input_img = np.expand_dims(input_img, axis=0)

            # 1. Main Classification
            pred = clf_model.predict(input_img, verbose=0)[0]
            pest_conf = float(np.max(pred))
            pest_label = CLASSES[np.argmax(pred)]

            # 2. Disease Type Classification
            disease_label = "Unknown"
            disease_conf = 0.0
            
            if pest_label.lower() != "healthy":
                try:
                    disease_pred = clf_type_model.predict(input_img, verbose=0)[0]
                    disease_conf = float(np.max(disease_pred))
                    disease_label = DISEASE_CLASSES[np.argmax(disease_pred)]
                    display_label = f"{pest_label} | {disease_label}"
                except:
                    display_label = pest_label
            else:
                display_label = pest_label

            # Save the result for this specific tree for the Report Generator
            tree_results[tree_counter] = {
                "pest": {"label": pest_label, "probability": pest_conf},
                "type": {"label": disease_label, "probability": disease_conf}
            }

            # 3. Draw Bounding Box & Text
            color = (0, 255, 0) if "healthy" in pest_label.lower() else (0, 0, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            text = f"ID {tree_counter} | {display_label} {pest_conf:.2f}"
            cv2.rectangle(frame, (x1, max(0, y1 - 25)), (x1 + 350, y1), color, -1)
            cv2.putText(frame, text, (x1 + 5, max(15, y1 - 7)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            tree_counter += 1

    # Save final image
    cv2.imwrite(output_path, frame)
    print(f"✅ Annotated image successfully saved to: {output_path}")

    return tree_results