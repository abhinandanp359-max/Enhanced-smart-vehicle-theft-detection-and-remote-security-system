"""
ai_engine/config.py - Configuration settings for the AI Vehicle Security Engine
"""
import os

# Video capture source: 0 for default webcam, or a path to a video file e.g., 'test_video.mp4'
VIDEO_SOURCE = int(os.getenv("VIDEO_SOURCE", 0))

# YOLO detection settings
YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.45))
TARGET_CLASS_ID = 0  # 0 corresponds to 'person' in standard COCO dataset

# Anti-False-Alarm Temporal Accumulator
# Time in seconds an intruder must continuously occupy the driver seat before triggering alarm
SUSTAINED_SECONDS = float(os.getenv("SUSTAINED_SECONDS", 3.0))

# Cooldown time in seconds after alarm fires before a new alarm can be triggered
ALARM_COOLDOWN_SECONDS = float(os.getenv("ALARM_COOLDOWN_SECONDS", 15.0))

# Driver Seat Region of Interest (ROI) polygon
# Normalized coordinates (x, y) where (0,0) is top-left and (1,1) is bottom-right
# Default polygon focuses on the center-right or center driver seat area
DEFAULT_ROI_POLYGON = [
    (0.20, 0.20),  # Top-left
    (0.80, 0.20),  # Top-right
    (0.85, 0.95),  # Bottom-right
    (0.15, 0.95),  # Bottom-left
]

# Alarm Siren Audio
SOUND_ENABLED = os.getenv("SOUND_ENABLED", "true").lower() == "true"

# Backend API Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000/api/incidents")
VEHICLE_ID = os.getenv("VEHICLE_ID", "veh_01")

# Evidence Storage Directory
EVIDENCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evidence")
os.makedirs(EVIDENCE_DIR, exist_ok=True)
