"""
ai_engine/detector.py - YOLOv8 Person Detector with Driver Seat ROI polygon gating
"""
import cv2
import numpy as np
from ultralytics import YOLO
from .config import YOLO_MODEL_PATH, CONFIDENCE_THRESHOLD, TARGET_CLASS_ID


class PersonDetector:
    def __init__(self, model_path=YOLO_MODEL_PATH, conf_thresh=CONFIDENCE_THRESHOLD, imgsz=384):
        self.conf_thresh = conf_thresh
        self.imgsz = imgsz
        print(f"[AI Detector] Loading YOLOv8 model from '{model_path}'...")
        self.model = YOLO(model_path)
        # Pre-warm model so live camera loop starts with zero lag
        print("[AI Detector] Warming up neural network...")
        dummy = np.zeros((self.imgsz, self.imgsz, 3), dtype=np.uint8)
        self.model.predict(source=dummy, imgsz=self.imgsz, verbose=False)
        print("[AI Detector] YOLOv8 engine is ready and optimized for real-time inference.")

    def detect(self, frame):
        """
        Run inference on frame.
        Returns a list of dicts:
        [{
            'bbox': (x1, y1, x2, y2),
            'confidence': float,
            'center': (cx, cy)
        }]
        """
        results = self.model.predict(
            source=frame,
            classes=[TARGET_CLASS_ID],  # 0 = person
            conf=self.conf_thresh,
            imgsz=self.imgsz,
            verbose=False
        )

        detections = []
        if not results:
            return detections

        first_res = results[0]
        boxes = first_res.boxes
        if boxes is None or len(boxes) == 0:
            return detections

        for box in boxes:
            xyxy = box.xyxy[0].cpu().numpy().astype(int)
            x1, y1, x2, y2 = xyxy
            conf = float(box.conf[0].cpu().numpy())
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            detections.append({
                'bbox': (x1, y1, x2, y2),
                'confidence': conf,
                'center': (cx, cy)
            })

        return detections

    @staticmethod
    def get_pixel_roi(frame_shape, normalized_roi):
        """Converts normalized ROI polygon points [(nx, ny), ...] to pixel integer coordinates."""
        h, w = frame_shape[:2]
        return np.array([(int(nx * w), int(ny * h)) for nx, ny in normalized_roi], dtype=np.int32)

    @staticmethod
    def is_in_roi(detection, pixel_roi):
        """
        Checks if detection is inside the ROI polygon.
        Considers either the center point OR upper body (driver chest/head).
        """
        cx, cy = detection['center']
        x1, y1, x2, y2 = detection['bbox']
        # Head / upper-chest point (25% down the box height)
        upper_point = (cx, int(y1 + 0.25 * (y2 - y1)))

        center_inside = cv2.pointPolygonTest(pixel_roi, (float(cx), float(cy)), False) >= 0
        upper_inside = cv2.pointPolygonTest(pixel_roi, (float(upper_point[0]), float(upper_point[1])), False) >= 0

        return center_inside or upper_inside
