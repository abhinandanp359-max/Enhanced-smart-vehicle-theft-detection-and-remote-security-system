"""
ai_engine/backend_client.py - Evidence snapshot saver, video uploader, and Phone Notification Dispatcher
Formats security events with event_type: "unauthorized_person", security_state: "alert",
image_id, and video_id.
"""
import json
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

    def save_snapshot(self, frame, prefix="theft_intruder"):
        """Save evidence snapshot image to disk with timestamp."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{self.vehicle_id}_{timestamp}.jpg"
        filepath = os.path.join(self.evidence_dir, filename)
        cv2.imwrite(filepath, frame)
        return filepath

    def dispatch_incident_async(self, snapshot_path, video_path=None, confidence=0.95, duration_seconds=3.0):
        """Asynchronously dispatches the incident report, image, and video to the backend and phone."""
        thread = threading.Thread(
            target=self._post_incident,
            args=(snapshot_path, video_path, confidence, duration_seconds),
            daemon=True
        )
        thread.start()

    def _post_incident(self, snapshot_path, video_path, confidence, duration_seconds):
        """Internal worker method to send multipart HTTP POST and simulate phone push alert."""
        timestamp_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        image_id = os.path.basename(snapshot_path) if snapshot_path else ""
        video_id = os.path.basename(video_path) if video_path else ""

        payload = {
            "event_type": "unauthorized_person",
            "timestamp": timestamp_iso,
            "image_id": image_id,
            "video_id": video_id,
            "security_state": "alert",
            "vehicle_id": self.vehicle_id,
            "confidence": f"{confidence:.2f}",
            "duration_seconds": f"{duration_seconds:.1f}"
        }

        # 1. Print formatted Phone Push Notification
        print("\n" + "=" * 68)
        print("📱 [PHONE NOTIFICATION SENT TO OWNER]")
        print(f"   • Event Type     : {payload['event_type'].upper()} ({payload['security_state'].upper()})")
        print(f"   • Timestamp      : {payload['timestamp']}")
        print(f"   • Captured Photo : {payload['image_id']}")
        if video_id:
            print(f"   • Captured Video : {payload['video_id']}")
        print(f"   • Security State : {payload['security_state'].upper()} (Emergency Siren Active)")
        print(f"   • Payload JSON   : {json.dumps(payload)}")
        print("=" * 68 + "\n")

        # 2. Upload to Backend Server (REST API)
        try:
            print(f"[Backend Client] Uploading evidence to {self.backend_url}...")
            files = {}
            if snapshot_path and os.path.exists(snapshot_path):
                files["snapshot"] = (image_id, open(snapshot_path, "rb"), "image/jpeg")
            if video_path and os.path.exists(video_path):
                files["video"] = (video_id, open(video_path, "rb"), "video/mp4")

            response = requests.post(self.backend_url, files=files, data=payload, timeout=5)
            if response.status_code in [200, 201]:
                print(f"[Backend Client] Server confirmed receipt: {response.text}")
            else:
                print(f"[Backend Client] Server returned status {response.status_code}: {response.text}")

            for f in files.values():
                f[1].close()

        except requests.exceptions.ConnectionError:
            print("[Backend Client] (Notice) Backend server not reachable. Image & Video preserved locally in:")
            print(f"                 {self.evidence_dir}")
        except Exception as e:
            print(f"[Backend Client] Error posting incident: {e}")
