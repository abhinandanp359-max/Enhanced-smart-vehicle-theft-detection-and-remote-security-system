"""
ai_engine/backend_client.py - Evidence snapshot saver and Backend incident dispatcher
Dispatches asynchronously in a background thread so video streaming never blocks.
"""
import os
import threading
import time
import cv2
import requests
from .config import BACKEND_URL, VEHICLE_ID, EVIDENCE_DIR


class BackendClient:
    def __init__(self, backend_url=BACKEND_URL, vehicle_id=VEHICLE_ID, evidence_dir=EVIDENCE_DIR):
        self.backend_url = backend_url
        self.vehicle_id = vehicle_id
        self.evidence_dir = evidence_dir
        os.makedirs(self.evidence_dir, exist_ok=True)

    def save_snapshot(self, frame, prefix="incident"):
        """Save evidence snapshot image to disk with timestamp."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{self.vehicle_id}_{timestamp}.jpg"
        filepath = os.path.join(self.evidence_dir, filename)
        cv2.imwrite(filepath, frame)
        return filepath

    def dispatch_incident_async(self, snapshot_path, confidence, duration_seconds):
        """Asynchronously dispatches the incident report and photo to the backend."""
        thread = threading.Thread(
            target=self._post_incident,
            args=(snapshot_path, confidence, duration_seconds),
            daemon=True
        )
        thread.start()

    def _post_incident(self, snapshot_path, confidence, duration_seconds):
        """Internal worker method to send multipart HTTP POST."""
        try:
            print(f"[Backend Client] Dispatching incident to {self.backend_url}...")
            with open(snapshot_path, "rb") as img_file:
                files = {"snapshot": (os.path.basename(snapshot_path), img_file, "image/jpeg")}
                data = {
                    "vehicleId": self.vehicle_id,
                    "confidence": f"{confidence:.2f}",
                    "durationSeconds": f"{duration_seconds:.1f}",
                    "eventType": "UNAUTHORIZED_OCCUPANCY",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
                response = requests.post(self.backend_url, files=files, data=data, timeout=4)
                if response.status_code in [200, 201]:
                    print(f"[Backend Client] Incident successfully received by backend: {response.text}")
                else:
                    print(f"[Backend Client] Backend returned status {response.status_code}: {response.text}")
        except requests.exceptions.ConnectionError:
            print("[Backend Client] (Notice) Backend server not reachable. Incident snapshot safely preserved locally at:")
            print(f"                 {snapshot_path}")
        except Exception as e:
            print(f"[Backend Client] Error posting incident: {e}")
