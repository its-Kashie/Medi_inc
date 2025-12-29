from ultralytics import YOLO
import cv2
import torch

# ---- SETTINGS ----
model1_path = "models/placenta_detector.pt"
model2_path = "models/waste_classifier.pt"   # 2nd model
video_path  = "videos/videoplayback.mp4"
output_path = "output_two_models.mp4"
device = "cuda" if torch.cuda.is_available() else "cpu"
conf = 0.25
# ------------------

# Load YOLO 11 Models
model1 = YOLO(model1_path)
model2 = YOLO(model2_path)

cap = cv2.VideoCapture(video_path)
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

color1 = (0, 255, 0)
color2 = (255, 0, 0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Run both YOLO models on GPU
    r1 = model1(frame, device=device, conf=conf)[0]
    r2 = model2(frame, device=device, conf=conf)[0]

    # Draw boxes from model 1
    for box in r1.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cv2.rectangle(frame, (x1,y1), (x2,y2), color1, 2)
        cv2.putText(frame, f"M1 {float(box.conf):.2f}", (x1, y1-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color1, 2)

    # Draw boxes from model 2
    for box in r2.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cv2.rectangle(frame, (x1,y1), (x2,y2), color2, 2)
        cv2.putText(frame, f"M2 {float(box.conf):.2f}", (x1, y1-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color2, 2)

    out.write(frame)

cap.release()
out.release()

print("FINISHED: Saved →", output_path)
