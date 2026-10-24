"""
ai_engine/backend_client.py - Evidence snapshot saver, video uploader, GPS telemetry,
and Telegram / WhatsApp Phone Notification Dispatcher.
Formats security events with rich JSON, live GPS coordinates, and dispatches to phone.
"""
import json
import os
import threading
import time
import urllib.parse
import cv2
import requests
from .config import (
    BACKEND_URL, VEHICLE_ID, EVIDENCE_DIR,
    GPS_MODE, VEHICLE_LATITUDE, VEHICLE_LONGITUDE, VEHICLE_LOCATION_NAME,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    WHATSAPP_PHONE, WHATSAPP_API_KEY
)


import subprocess


_LIVE_GPS_CACHE = None
_LIVE_GPS_CACHE_TIME = 0
_GEOCODE_CACHE = {}


def fetch_live_system_gps():
    """
    Dynamically queries live hardware / Windows GPS & Wi-Fi positioning.
    Runs silently in real-time wherever the vehicle or laptop travels without asking the user.
    """
    global _LIVE_GPS_CACHE, _LIVE_GPS_CACHE_TIME
    now = time.time()
    if _LIVE_GPS_CACHE and (now - _LIVE_GPS_CACHE_TIME < 45):
        return _LIVE_GPS_CACHE

    try:
        ps_script = (
            "Add-Type -AssemblyName System.Device; "
            "$w = New-Object System.Device.Location.GeoCoordinateWatcher; "
            "$w.Start(); "
            "for ($i=0; $i -lt 15; $i++) { "
            "if ($w.Status -eq [System.Device.Location.GeoPositionStatus]::Ready) { break }; "
            "Start-Sleep -Milliseconds 150 "
            "}; "
            "$loc = $w.Position.Location; "
            "[PSCustomObject]@{ Status = $w.Status.ToString(); Latitude = $loc.Latitude; Longitude = $loc.Longitude; IsUnknown = $loc.IsUnknown } | ConvertTo-Json; "
            "$w.Stop()"
        )
        cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if p.returncode == 0 and p.stdout.strip():
            data = json.loads(p.stdout)
            if not data.get("IsUnknown", True):
                lat = float(data.get("Latitude", 0))
                lon = float(data.get("Longitude", 0))
                if lat != 0 and lon != 0:
                    loc_name = f"Live Vehicle GPS ({lat:.4f}, {lon:.4f})"
                    try:
                        rev_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat:.5f}&lon={lon:.5f}"
                        req = urllib.request.Request(rev_url, headers={"User-Agent": "VehicleSecurityBot/1.0"})
                        with urllib.request.urlopen(req, timeout=3.5) as r:
                            geo_res = json.loads(r.read().decode())
                            addr = geo_res.get("address", {})
                            road = addr.get("road") or addr.get("suburb") or addr.get("neighbourhood") or ""
                            city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county") or ""
                            state = addr.get("state") or ""
                            parts = [p for p in [road, city, state] if p]
                            if parts:
                                loc_name = ", ".join(parts)
                    except Exception:
                        pass

                    result = {
                        "latitude": round(lat, 6),
                        "longitude": round(lon, 6),
                        "location_name": loc_name,
                        "google_maps_url": f"https://www.google.com/maps?q={lat:.6f},{lon:.6f}",
                        "status": "LIVE_DYNAMIC_GPS"
                    }
                    _LIVE_GPS_CACHE = result
                    _LIVE_GPS_CACHE_TIME = now
                    print(f"[GPS] Dynamic vehicle location detected: {loc_name} ({lat:.6f}, {lon:.6f})")
                    return result
    except Exception:
        pass

    return None


def geocode_college_name(name):
    """Automatically finds exact satellite GPS coordinates from college name with zero manual setup."""
    if not name or name in _GEOCODE_CACHE:
        return _GEOCODE_CACHE.get(name)

    # Skip generic placeholders
    if name in ["College Campus - Main Parking Bay", "Driver Seat - Vehicle Bay 1"]:
        return None

    try:
        url = "https://photon.komoot.io/api/?q=" + urllib.parse.quote(name) + "&limit=1"
        req = urllib.request.Request(url, headers={"User-Agent": "VehicleSecurityBot/1.0"})
        with urllib.request.urlopen(req, timeout=3.5) as res:
            data = json.loads(res.read().decode())
            features = data.get("features", [])
            if features:
                coords = features[0]["geometry"]["coordinates"]
                lon, lat = float(coords[0]), float(coords[1])
                props = features[0].get("properties", {})
                display_name = props.get("name") or name
                city = props.get("city") or props.get("state") or ""
                full_name = f"{display_name}, {city}" if city else display_name
                result = (lat, lon, full_name)
                _GEOCODE_CACHE[name] = result
                print(f"[GPS] Automatically resolved '{name}' to exact coordinates: {lat:.6f}, {lon:.6f}")
                return result
    except Exception:
        pass

    return None


def fetch_gps_telemetry():
    """
    Dynamically retrieves exact vehicle GPS coordinates:
    1. First: Queries live Windows & Wi-Fi positioning hardware (works dynamically anywhere you go, zero user questions).
    2. Second: If college name is configured, queries OpenStreetMap geocoder.
    3. Fallback: Configured default coordinates.
    """
    # 1. Real-time dynamic location (detects wherever you drive or test without asking)
    live_gps = fetch_live_system_gps()
    if live_gps:
        return live_gps

    # 2. College campus geocoding (if COLLEGE_NAME is set in .env)
    loc_name = os.getenv("COLLEGE_NAME") or (VEHICLE_LOCATION_NAME if VEHICLE_LOCATION_NAME not in ["College Campus - Main Parking Bay", "Driver Seat - Vehicle Bay 1"] else "")
    if loc_name:
        auto_coords = geocode_college_name(loc_name)
        if auto_coords:
            lat, lon, resolved_name = auto_coords
            return {
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "location_name": resolved_name,
                "google_maps_url": f"https://www.google.com/maps?q={lat:.6f},{lon:.6f}",
                "status": "AUTO_RESOLVED_CAMPUS_GPS"
            }

    # 3. Static fallback
    return {
        "latitude": round(VEHICLE_LATITUDE, 6),
        "longitude": round(VEHICLE_LONGITUDE, 6),
        "location_name": VEHICLE_LOCATION_NAME,
        "google_maps_url": f"https://www.google.com/maps?q={VEHICLE_LATITUDE:.6f},{VEHICLE_LONGITUDE:.6f}",
        "status": "CONFIG_DEFAULT_GPS"
    }



class BackendClient:
    def __init__(self, backend_url=BACKEND_URL, vehicle_id=VEHICLE_ID, evidence_dir=EVIDENCE_DIR):
        self.backend_url = backend_url
        self.vehicle_id = vehicle_id
        self.evidence_dir = evidence_dir
        self.pending_video_threads = []
        os.makedirs(self.evidence_dir, exist_ok=True)

    def save_snapshot(self, frame, prefix="theft_intruder"):
        """Save evidence snapshot image to disk with timestamp."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{self.vehicle_id}_{timestamp}.jpg"
        filepath = os.path.join(self.evidence_dir, filename)
        cv2.imwrite(filepath, frame)
        return filepath

    def dispatch_incident_async(self, snapshot_path, video_path=None, confidence=0.95, duration_seconds=3.0):
        """Asynchronously dispatches the incident report, image, and GPS alerts to phone and backend."""
        thread = threading.Thread(
            target=self._post_incident,
            args=(snapshot_path, video_path, confidence, duration_seconds),
            daemon=True
        )
        thread.start()

    def dispatch_video_async(self, video_path):
        """Asynchronously dispatches the recorded 5-second MP4 video clip to Telegram."""
        if not video_path or not os.path.exists(video_path):
            return
        thread = threading.Thread(
            target=self._upload_video_worker,
            args=(video_path,),
            daemon=False
        )
        self.pending_video_threads.append(thread)
        thread.start()

    def wait_for_pending_uploads(self, timeout=15):
        """Ensures any in-flight video clip uploads finish uploading before exiting."""
        for t in list(self.pending_video_threads):
            if t.is_alive():
                print("[Telegram] Finishing video clip upload to phone before closing...")
                t.join(timeout=timeout)

    def _upload_video_worker(self, video_path):
        """Worker thread to deliver MP4 video clip to Telegram phone."""
        chat_id = TELEGRAM_CHAT_ID or os.getenv("TELEGRAM_CHAT_ID", "")
        token = TELEGRAM_BOT_TOKEN or os.getenv("TELEGRAM_BOT_TOKEN", "")
        if not token or not chat_id:
            return

        bot_url = f"https://api.telegram.org/bot{token}"
        print(f"[Telegram] Uploading 5s incident video clip to your phone: {os.path.basename(video_path)}...")
        try:
            with open(video_path, "rb") as video_file:
                vr = requests.post(
                    f"{bot_url}/sendVideo",
                    data={
                        "chat_id": chat_id,
                        "caption": "📹 <b>5-Second Intruder Video Evidence Clip</b>\nVehicle: <code>veh_01</code>",
                        "parse_mode": "HTML"
                    },
                    files={"video": video_file},
                    timeout=60
                )
                if vr.status_code == 200:
                    print("[OK] [Telegram] Incident video clip delivered to your phone successfully!")
                else:
                    print(f"[Telegram] Video send status {vr.status_code}: {vr.text}")
        except Exception as e:
            print(f"[Telegram] Error delivering video to phone: {e}")

        # Also deliver video clip to Mobile App backend server
        try:
            with open(video_path, "rb") as video_file:
                video_endpoint = f"{self.backend_url}/video"
                vr_backend = requests.post(
                    video_endpoint,
                    files={"video": (os.path.basename(video_path), video_file, "video/mp4")},
                    data={"video_id": os.path.basename(video_path), "vehicle_id": self.vehicle_id},
                    timeout=15
                )
                if vr_backend.status_code in [200, 201]:
                    print(f"[OK] [Mobile App] Incident video clip linked to phone app: {os.path.basename(video_path)}")
        except Exception:
            pass

    def _post_incident(self, snapshot_path, video_path, confidence, duration_seconds):
        """Internal worker method: builds rich JSON, sends Telegram/WhatsApp, and uploads to backend."""
        timestamp_iso = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        if not timestamp_iso.endswith("Z") and not ("+" in timestamp_iso[-6:] or "-" in timestamp_iso[-6:]):
            timestamp_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        image_id = os.path.basename(snapshot_path) if snapshot_path else ""
        video_id = os.path.basename(video_path) if video_path else ""
        gps_data = fetch_gps_telemetry()

        # Comprehensive JSON incident payload with GPS telemetry
        payload = {
            "event_type": "unauthorized_person",
            "security_state": "CRITICAL_THEFT_ALERT",
            "vehicle_id": self.vehicle_id,
            "timestamp": timestamp_iso,
            "confidence": f"{confidence:.2f}",
            "duration_seconds": f"{duration_seconds:.1f}",
            "image_id": image_id,
            "video_id": video_id,
            "gps": gps_data,
            "hardware_telemetry": {
                "siren": "ACTIVE_HIGH_DECIBEL",
                "esp32_relay": "TRIGGERED",
                "cabin_roi": "BREACHED"
            }
        }

        # 1. Archive JSON Telemetry File Permanently
        json_filename = f"{os.path.splitext(image_id)[0] if image_id else 'theft_incident'}.json"
        json_filepath = os.path.join(self.evidence_dir, json_filename)
        try:
            with open(json_filepath, "w") as jf:
                json.dump(payload, jf, indent=2)
        except Exception as e:
            print(f"[Backend Client] Warning saving JSON: {e}")

        # 2. Print formatted Phone Push Notification & JSON to console
        print("\n" + "=" * 70)
        print("[INSTANT PHONE SECURITY ALERT DISPATCHED]")
        print("=" * 70)
        print(f"   * Event Type     : {payload['event_type'].upper()} ({payload['security_state']})")
        print(f"   * Vehicle ID     : {payload['vehicle_id']}")
        print(f"   * Timestamp      : {payload['timestamp']}")
        print(f"   * Location       : {gps_data['location_name']}")
        print(f"   * Coordinates    : {gps_data['latitude']}, {gps_data['longitude']}")
        print(f"   * Google Maps    : {gps_data['google_maps_url']}")
        print(f"   * Captured Photo : {payload['image_id']}")
        if video_id:
            print(f"   * Captured Video : {payload['video_id']}")
        print(f"   * Evidence JSON  : {json_filename}")
        print("\n--- RICH INCIDENT JSON PAYLOAD ---")
        print(json.dumps(payload, indent=2))
        print("=" * 70 + "\n")

        # 3. Send Telegram Bot Mobile Notification (Photo + Video + Location)
        self._send_telegram_alert(payload, snapshot_path, video_path)

        # 4. Send WhatsApp Notification
        self._send_whatsapp_alert(payload)

        # 5. Upload Evidence and JSON to Backend Server (REST API)
        try:
            print(f"[Backend Client] Uploading evidence to {self.backend_url}...")
            files = {}
            if snapshot_path and os.path.exists(snapshot_path):
                files["snapshot"] = (image_id, open(snapshot_path, "rb"), "image/jpeg")
            if video_path and os.path.exists(video_path):
                files["video"] = (video_id, open(video_path, "rb"), "video/mp4")

            post_data = {"payload_json": json.dumps(payload), **payload}
            response = requests.post(self.backend_url, files=files, data=post_data, timeout=5)
            if response.status_code in [200, 201]:
                print(f"[Backend Client] Server confirmed receipt: {response.text}")
            else:
                print(f"[Backend Client] Server returned status {response.status_code}: {response.text}")

            for f in files.values():
                f[1].close()

        except requests.exceptions.ConnectionError:
            print("[Backend Client] (Notice) Backend server not reachable. Evidence safely preserved in:")
            print(f"                 {self.evidence_dir}")
        except Exception as e:
            print(f"[Backend Client] Error posting incident: {e}")

    def _send_telegram_alert(self, payload, snapshot_path, video_path):
        """Dispatches rich Telegram mobile alert with intruder photo, video, and GPS maps link."""
        if not TELEGRAM_BOT_TOKEN:
            print("[Telegram] Bot token not set.")
            return

        chat_id = TELEGRAM_CHAT_ID
        bot_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

        # If CHAT_ID is not configured, automatically detect it from latest /start or message
        if not chat_id:
            try:
                updates = requests.get(f"{bot_url}/getUpdates", timeout=4).json()
                results = updates.get("result", [])
                if results:
                    last_update = results[-1]
                    msg_obj = last_update.get("message") or last_update.get("my_chat_member")
                    if msg_obj and "chat" in msg_obj:
                        chat_id = str(msg_obj["chat"]["id"])
                        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
                        if os.path.exists(env_file):
                            try:
                                with open(env_file, "r", encoding="utf-8") as ef:
                                    txt = ef.read()
                                if "TELEGRAM_CHAT_ID=" in txt:
                                    txt = txt.replace("TELEGRAM_CHAT_ID=", f"TELEGRAM_CHAT_ID={chat_id}")
                                    with open(env_file, "w", encoding="utf-8") as ef:
                                        ef.write(txt)
                            except Exception:
                                pass
                        print(f"[Telegram] Auto-detected Telegram Chat ID: {chat_id} and saved to .env!")
                else:
                    print("\n[Telegram Alert Ready] Please open your bot on Telegram: @Hellomycar_bot and tap 'START' once!")
                    return
            except Exception as e:
                print(f"[Telegram] Could not auto-fetch Chat ID: {e}")
                return

        caption = (
            f"🚨 <b>CRITICAL VEHICLE THEFT ALERT!</b> 🚨\n\n"
            f"🚗 <b>Vehicle ID:</b> <code>{payload['vehicle_id']}</code>\n"
            f"⚠️ <b>Status:</b> <b>UNAUTHORIZED INTRUDER IN DRIVER SEAT</b>\n"
            f"⏱️ <b>Duration:</b> {payload['duration_seconds']}s (Siren Triggered)\n"
            f"🎯 <b>Confidence:</b> {int(float(payload['confidence']) * 100)}%\n"
            f"🕒 <b>Time:</b> {payload['timestamp']}\n\n"
            f"📍 <b>Location:</b> {payload['gps']['location_name']}\n"
            f"🌐 <a href=\"{payload['gps']['google_maps_url']}\">Open in Google Maps</a>\n\n"
            f"📢 <b>Action:</b> High-decibel alarm sounding! Police evidence recorded."
        )

        # 1. Send Intruder Photo (High Priority)
        try:
            if snapshot_path and os.path.exists(snapshot_path):
                with open(snapshot_path, "rb") as photo_file:
                    r = requests.post(
                        f"{bot_url}/sendPhoto",
                        data={"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"},
                        files={"photo": photo_file},
                        timeout=30
                    )
                    if r.status_code == 200:
                        print("[OK] [Telegram] Incident photo alert sent to phone successfully!")
                    else:
                        print(f"[Telegram] Photo send response: {r.text}")
            else:
                requests.post(
                    f"{bot_url}/sendMessage",
                    data={"chat_id": chat_id, "text": caption, "parse_mode": "HTML"},
                    timeout=15
                )
        except Exception as e:
            print(f"[Telegram] Error sending photo alert: {e}")

        # 2. Send 5-Second HD Video Evidence Clip
        try:
            if video_path and os.path.exists(video_path):
                print("[Telegram] Uploading incident video clip to phone...")
                with open(video_path, "rb") as video_file:
                    vr = requests.post(
                        f"{bot_url}/sendVideo",
                        data={
                            "chat_id": chat_id,
                            "caption": "📹 <b>5-Second Intruder Video Clip (Cabin Evidence)</b>",
                            "parse_mode": "HTML"
                        },
                        files={"video": video_file},
                        timeout=60
                    )
                    if vr.status_code == 200:
                        print("[OK] [Telegram] Video evidence clip sent to phone successfully!")
                    else:
                        print(f"[Telegram] Video send response: {vr.text}")
        except Exception as e:
            print(f"[Telegram] Error sending video clip: {e}")

    def _send_whatsapp_alert(self, payload):
        """Sends instant WhatsApp alert via CallMeBot webhook if configured."""
        if not WHATSAPP_PHONE or not WHATSAPP_API_KEY:
            return

        msg = (
            f"CRITICAL VEHICLE THEFT ALERT!\n"
            f"Vehicle: {payload['vehicle_id']}\n"
            f"Status: Intruder Detected in Driver Seat!\n"
            f"Time: {payload['timestamp']}\n"
            f"Location: {payload['gps']['location_name']}\n"
            f"GPS Map: {payload['gps']['google_maps_url']}\n"
            f"Alarm Siren: ACTIVE"
        )
        try:
            encoded_msg = urllib.parse.quote(msg)
            url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_PHONE}&text={encoded_msg}&apikey={WHATSAPP_API_KEY}"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                print("[OK] [WhatsApp] Instant alert dispatched to phone successfully!")
        except Exception as e:
            print(f"[WhatsApp] Notification error: {e}")

