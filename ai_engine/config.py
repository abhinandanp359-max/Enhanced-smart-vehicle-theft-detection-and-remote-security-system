"""
ai_engine/config.py - Configuration settings for the AI Vehicle Security Engine
"""
import os

# Automatically load .env file if present in workspace root
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(_env_path):
    try:
        with open(_env_path, "r", encoding="utf-8") as _ef:
            for _line in _ef:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    _k = _k.strip()
                    _v = _v.strip().strip('"').strip("'")
                    if _k not in os.environ:
                        os.environ[_k] = _v
    except Exception:
        pass

# Video capture source: 0 for default webcam, integer for other camera index,
# or a full URL string for IP/phone camera stream.
_raw_source = os.getenv("VIDEO_SOURCE", "0")
VIDEO_SOURCE = int(_raw_source) if _raw_source.isdigit() else _raw_source


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

# Vehicle GPS Telemetry Configuration (College / Vehicle Exact Location)
GPS_MODE = os.getenv("GPS_MODE", "EXACT").upper()
VEHICLE_LATITUDE = float(os.getenv("VEHICLE_LATITUDE", os.getenv("DEFAULT_LATITUDE", "12.9716")))
VEHICLE_LONGITUDE = float(os.getenv("VEHICLE_LONGITUDE", os.getenv("DEFAULT_LONGITUDE", "77.5946")))
VEHICLE_LOCATION_NAME = os.getenv("VEHICLE_LOCATION_NAME", "College Campus - Main Parking Area")


# Instant Mobile Alerts (Telegram / WhatsApp)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
WHATSAPP_PHONE = os.getenv("WHATSAPP_PHONE", "")
WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY", "")

# Evidence Storage Directory
EVIDENCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evidence")
os.makedirs(EVIDENCE_DIR, exist_ok=True)

