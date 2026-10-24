"""
ai_engine/main.py - Professional Automotive Cyber-Security Vehicle Theft Detection Engine
Features:
  1. Deep Face Verification (YuNet + MobileNetV3) with Temporal Smoothing.
  2. Tactical Corner-Bracket Reticles & Real-Time Identity Match Gauge.
  3. Gated Siren Deterrent & Auto-Evidence Dispatch (Triggers ONLY on Unauthorized Intruders).
  4. 100% Fully Automated (Runs independently with zero manual keyboard controls).
"""
import argparse
import sys
import time
import requests
import cv2
import numpy as np

from .config import (
    VIDEO_SOURCE,
    DEFAULT_ROI_POLYGON,
    SUSTAINED_SECONDS,
    SOUND_ENABLED,
)
from .detector import PersonDetector
from .state_machine import TheftStateMachine, SystemMode, DetectionState
from .sound_alarm import AlarmSiren
from .backend_client import BackendClient
from .biometric_authenticator import BiometricAuthenticator
from .eye_authenticator import EyeAuthenticator
from .video_recorder import VideoEvidenceRecorder
from .hardware_controller import ESP32Controller


def draw_corner_brackets(img, x, y, w, h, color, length=18, thickness=2):
    """Draws sleek tactical corner brackets around a target bounding box."""
    # Top-Left
    cv2.line(img, (x, y), (x + length, y), color, thickness)
    cv2.line(img, (x, y), (x, y + length), color, thickness)
    # Top-Right
    cv2.line(img, (x + w, y), (x + w - length, y), color, thickness)
    cv2.line(img, (x + w, y), (x + w, y + length), color, thickness)
    # Bottom-Left
    cv2.line(img, (x, y + h), (x + length, y + h), color, thickness)
    cv2.line(img, (x, y + h), (x, y + h - length), color, thickness)
    # Bottom-Right
    cv2.line(img, (x + w, y + h), (x + w - length, y + h), color, thickness)
    cv2.line(img, (x + w, y + h), (x + w, y + h - length), color, thickness)


def draw_professional_hud(frame, sm_status, pixel_roi, detections, face_box, landmarks, auth_score, fps):
    """Renders an automotive/military cyber-security HUD overlay."""
    h, w = frame.shape[:2]
    state = sm_status['state']
    elapsed = sm_status['elapsed']
    threshold = sm_status['threshold']
    driver_name = sm_status.get('driver_name', 'Unknown')
    mode = sm_status.get('mode', SystemMode.ARMED)
    is_auth = sm_status.get('is_authorized', False)

    # 1. State Styling
    if mode == SystemMode.TRUSTED_DRIVER:
        theme_color = (0, 190, 255)      # Amber / Gold
        status_text = "SECURITY STATUS: TRUSTED DRIVER ACTIVE [SIREN BYPASSED]"
        status_bg = (0, 120, 180)
    elif mode == SystemMode.DISARMED:
        theme_color = (120, 120, 120)    # Neutral Grey
        status_text = "SECURITY STATUS: SYSTEM DISARMED [SURVEILLANCE PAUSED]"
        status_bg = (60, 60, 60)
    elif state == DetectionState.CLEAR:
        theme_color = (0, 220, 0)        # Neon Green (Secure)
        status_text = "SECURITY STATUS: ARMED [CABIN MONITORED - ALL CLEAR]"
        status_bg = (0, 130, 0)
    elif state == DetectionState.AUTHORIZED_DRIVER:
        theme_color = (0, 255, 120)    # Emerald Green
        status_text = f"ACCESS GRANTED: AUTHORIZED OWNER [{driver_name.upper()}] - MATCH: {int(auth_score * 100)}%"
        status_bg = (0, 150, 40)
    elif state == DetectionState.ACCUMULATING:
        theme_color = (0, 80, 255)     # Warning Amber-Red
        progress = min(1.0, elapsed / max(0.1, threshold))
        status_text = f"ALERT: UNAUTHORIZED INTRUDER [{elapsed:.1f}s / {threshold:.1f}s] ({int(progress * 100)}%)"
        status_bg = (0, 60, 220)
    elif state == DetectionState.ALARM_ACTIVE:
        flash = int(time.time() * 6) % 2 == 0
        theme_color = (0, 0, 255) if flash else (255, 255, 255)
        status_text = "CRITICAL THEFT ALERT: INTRUDER IN DRIVER SEAT! SIREN ACTIVE!"
        status_bg = (0, 0, 230)
    else:  # COOLDOWN
        theme_color = (255, 120, 0)
        status_text = f"SECURITY BREACH LOGGED [COOLDOWN: {int(threshold - elapsed)}s]"
        status_bg = (180, 80, 0)

    # 2. Semi-Transparent Driver Cabin Polygon
    overlay = frame.copy()
    cv2.fillPoly(overlay, [pixel_roi], theme_color)
    cv2.addWeighted(overlay, 0.10, frame, 0.90, 0, frame)
    cv2.polylines(frame, [pixel_roi], isClosed=True, color=theme_color, thickness=2)

    # Label on top edge of Cabin Zone
    top_center = (int(np.mean(pixel_roi[:, 0])), int(np.min(pixel_roi[:, 1])) - 8)
    cv2.putText(frame, "DRIVER ZONE", (top_center[0] - 45, max(20, top_center[1])),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, theme_color, 1, cv2.LINE_AA)

    # 3. Person Detection Bounding Box (Subtle)
    for det in detections:
        x1, y1, x2, y2 = det['bbox']
        conf = det['confidence']
        box_color = (0, 255, 120) if is_auth else ((0, 0, 255) if state in [DetectionState.ACCUMULATING, DetectionState.ALARM_ACTIVE] else (0, 200, 255))
        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 1)
        # Position occupant confidence label at bottom-left of body box to avoid collision with face tag
        cv2.putText(frame, f"Occupant: {int(conf * 100)}%", (x1 + 6, min(h - 45, y2 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, box_color, 1, cv2.LINE_AA)

    # 4. Tactical Biometric Face Reticle & Facial Landmarks
    if face_box and face_box[2] >= 25:
        fx, fy, fw, fh = face_box
        reticle_color = (0, 255, 120) if is_auth else (0, 0, 255)

        # Draw professional corner brackets around face
        draw_corner_brackets(frame, fx, fy, fw, fh, reticle_color, length=16, thickness=2)

        # Draw facial landmark points (eyes, nose, mouth)
        for lx, ly in landmarks:
            cv2.circle(frame, (lx, ly), 2, reticle_color, -1)

        # Identity Tag:
        # For authorized owner: shows high biometric match percentage
        # For unauthorized intruder: shows ACCESS DENIED or Owner Match percentage
        if is_auth:
            tag = f"AUTHORIZED OWNER [{int(auth_score * 100)}% MATCH]"
        else:
            tag = "UNAUTHORIZED INTRUDER [ACCESS DENIED]" if auth_score < 0.15 else f"UNAUTHORIZED INTRUDER [Match: {int(auth_score * 100)}%]"

        # Draw dark contrast pill behind text for ultra-crisp visibility
        (tw, th), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.50, 2)
        tag_y = max(25, fy - 10)
        cv2.rectangle(frame, (fx - 10, tag_y - th - 5), (fx - 10 + tw + 8, tag_y + 4), (0, 0, 0), -1)
        cv2.putText(frame, tag, (fx - 6, tag_y - 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, reticle_color, 2, cv2.LINE_AA)

    # 5. Top Cyber-Security Status Banner
    cv2.rectangle(frame, (0, 0), (w, 38), status_bg, -1)
    cv2.putText(frame, status_text, (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 2, cv2.LINE_AA)

    # FPS counter on top right
    cv2.putText(frame, f"FPS: {fps:.0f}", (w - 85, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (255, 255, 255), 1, cv2.LINE_AA)

    # 6. Countdown Progress Bar for Unauthorized Intruder
    if state == DetectionState.ACCUMULATING:
        bar_w = int(w * 0.7)
        bar_h = 10
        bx = int((w - bar_w) / 2)
        by = 44
        filled_w = int(bar_w * min(1.0, elapsed / threshold))
        cv2.rectangle(frame, (bx, by), (bx + bar_w, by + bar_h), (30, 30, 30), -1)
        cv2.rectangle(frame, (bx, by), (bx + filled_w, by + bar_h), (0, 0, 255), -1)

    # 7. Bottom Tactical Telemetry Bar
    cv2.rectangle(frame, (0, h - 28), (w, h), (18, 18, 18), -1)
    telemetry_str = f"TELEMETRY: SENSORS ACTIVE | SIREN: {'RINGING' if state == DetectionState.ALARM_ACTIVE else 'STANDBY'} | QUIT: [Q]"
    cv2.putText(frame, telemetry_str, (15, h - 9), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (190, 190, 190), 1, cv2.LINE_AA)

    return frame


def run_pipeline(source=VIDEO_SOURCE, sustained_sec=SUSTAINED_SECONDS, sound_on=SOUND_ENABLED, headless=False):
    """Main video capture, detection, biometric verification, and decision pipeline loop."""
    print("=" * 68)
    print("  SMART VEHICLE THEFT DETECTION - AI VISION & BIOMETRIC ENGINE  ")
    print("=" * 68)
    print(f"  • Video Source     : {source}")
    print(f"  • Theft Threshold  : {sustained_sec}s sustained unauthorized presence")
    print(f"  • Siren Deterrent  : {'Enabled' if sound_on else 'Disabled'}")
    print("=" * 68)

    detector = PersonDetector()
    state_machine = TheftStateMachine(sustained_seconds=sustained_sec)
    siren = AlarmSiren(enabled=sound_on)
    backend = BackendClient()
    authenticator = BiometricAuthenticator()
    eye_auth = EyeAuthenticator()
    recorder = VideoEvidenceRecorder(pre_event_seconds=3.0, fps=20)
    hardware = ESP32Controller()
    owner_greeted = False

    if not authenticator.is_enrolled():
        print("\n" + "!" * 68)
        print(">>> NOTICE: No Owner Face Enrolled Yet! <<<")
        print("    Please run the training script first:")
        print("    -> python -m ai_engine.train")
        print("!" * 68 + "\n")

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[ERROR] Could not open video source: {source}")
        return

    prev_time = time.time()
    fps = 0.0

    window_name = "Vehicle Security - Driver Cabin Surveillance"
    if not headless:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 840, 520)

    print("\n[AI Engine] Surveillance system running automatically.")
    print("  • Authorized Owner   -> Green access granted, silent, safe.")
    print("  • Unauthorized Thief -> Red alert, 3s countdown, then siren + photo & video capture.")
    print("  • Press 'Q' to exit.\n")

    last_state_poll = 0.0
    last_stream_push = 0.0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                # Only loop for local video files, not live cameras or IP streams
                if isinstance(source, str) and not source.startswith("http") and not source.isdigit():
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break

            now = time.time()
            fps = 1.0 / max(0.001, (now - prev_time))
            prev_time = now

            # Sync remote security state (ARMED / DISARMED / TRUSTED_DRIVER / SIREN) from phone app
            if now - last_state_poll > 1.0:
                last_state_poll = now
                try:
                    r = requests.get("http://localhost:5000/api/security/state", timeout=0.25)
                    if r.status_code == 200:
                        data = r.json()
                        remote_mode = data.get("state", "ARMED")
                        remote_alarm = Boolean = data.get("alarmActive", False)

                        # Remote Siren Override
                        if remote_alarm and not siren.is_playing():
                            siren.start()
                            esp32.trigger_alarm()
                        elif not remote_alarm and siren.is_playing() and state_machine.detection_state != DetectionState.ALARM_ACTIVE:
                            siren.stop()
                            esp32.silence_alarm()

                        if remote_mode == "TRUSTED_DRIVER" and state_machine.system_mode != SystemMode.TRUSTED_DRIVER:
                            state_machine.set_trusted_driver()
                        elif remote_mode == "DISARMED" and state_machine.system_mode != SystemMode.DISARMED:
                            state_machine.disarm()
                        elif remote_mode == "ARMED" and state_machine.system_mode != SystemMode.ARMED:
                            state_machine.arm()
                except Exception:
                    pass

            # Feed frame to rolling video buffer
            recorder.add_frame(frame)

            pixel_roi = detector.get_pixel_roi(frame.shape, DEFAULT_ROI_POLYGON)

            # 1. Detect Persons using YOLOv8
            detections = detector.detect(frame)

            # 2. Check if any person occupies the Driver Seat ROI
            person_in_roi = False
            top_conf = 0.0
            target_person = None
            for det in detections:
                if detector.is_in_roi(det, pixel_roi):
                    person_in_roi = True
                    target_person = det
                    top_conf = max(top_conf, det['confidence'])

            # 3. High-Precision Biometric Verification
            is_authorized = False
            driver_name = "Unauthorized Intruder"
            auth_score = 0.0
            face_box = (0, 0, 0, 0)
            landmarks = []

            if person_in_roi and target_person is not None:
                is_authorized, driver_name, auth_score, face_box, landmarks = authenticator.authenticate(
                    frame, target_person['bbox']
                )

                # Secondary Ocular Confirmation (Strict Multi-Factor Gate):
                # Eye biometrics can ONLY strengthen an already authenticated face;
                # it is STRICTLY FORBIDDEN from authorizing an unknown face or intruder.
                if is_authorized and eye_auth.is_enrolled() and face_box[2] >= 25:
                    fx, fy, fw, fh = face_box
                    h_fr, w_fr = frame.shape[:2]
                    face_crop = frame[max(0, fy):min(h_fr, fy + fh), max(0, fx):min(w_fr, fx + fw)]
                    eye_ok, eye_score = eye_auth.authenticate(face_crop)
                    if eye_ok:
                        driver_name = "Owner (Dual-Factor Confirmed)"
            else:
                # Seat is vacant: instantly purge biometric history so next occupant is evaluated cleanly
                authenticator.reset()

            # 4. Multi-Factor Theft State Machine
            sm_status = state_machine.update(
                person_in_roi=person_in_roi,
                is_authorized=is_authorized,
                driver_name=driver_name,
                confidence=top_conf
            )

            # Ensure siren and ESP32 stay silent if authorized owner is detected
            if is_authorized:
                if siren.is_playing():
                    siren.stop()
                hardware.silence_alarm()
                if not owner_greeted:
                    hardware.grant_access()
                    owner_greeted = True
            else:
                owner_greeted = False

            # 5. Trigger Siren & Auto-Capture Photo AND Video if Unauthorized Intruder stays >= 3.0s
            if sm_status['trigger_alarm_now']:
                print("\n" + "!" * 68)
                print(">>> [CRITICAL SECURITY BREACH] UNAUTHORIZED INTRUDER CONFIRMED! <<<")
                print(f"    Confidence: {sm_status['highest_confidence']:.2f} | Duration: {sm_status['elapsed']:.1f}s")
                print("!" * 68 + "\n")

                # Sound emergency siren and trigger ESP32 hardware
                siren.start()
                hardware.trigger_alarm()

                # A. Save evidence photo with tactical HUD markings
                annotated_evidence = frame.copy()
                annotated_evidence = draw_professional_hud(
                    annotated_evidence, sm_status, pixel_roi, detections, face_box, landmarks, auth_score, fps
                )
                snapshot_file = backend.save_snapshot(annotated_evidence, prefix="theft_intruder")
                print(f"[AI Engine] Evidence photo captured & saved to: {snapshot_file}")

                # B. IMMEDIATELY dispatch Photo & GPS JSON alert to phone without waiting
                conf_val = sm_status['highest_confidence']
                dur_val = sm_status['elapsed']
                backend.dispatch_incident_async(
                    snapshot_path=snapshot_file,
                    video_path=None,
                    confidence=conf_val,
                    duration_seconds=dur_val
                )

                # C. Record incident MP4 video clip (pre-alarm buffer + 2.5s post-alarm footage):
                # As soon as video is encoded, dispatches the MP4 video clip to Telegram!
                def on_video_ready(video_filepath):
                    backend.dispatch_video_async(video_filepath)

                recorder.record_incident_clip(post_event_seconds=2.5, on_complete=on_video_ready)

            # 6. Real-Time Tactical HUD & Live Camera Stream Push (~7-8 FPS)
            hud_frame = draw_professional_hud(
                frame.copy(), sm_status, pixel_roi, detections, face_box, landmarks, auth_score, fps
            )

            # Push live camera feed to backend for phone app viewing
            if now - last_stream_push > 0.12:
                last_stream_push = now
                def _push_live_frame(f_to_send):
                    try:
                        # 640x360 @ 55% quality is ~15KB per frame: ultra low latency and silky smooth
                        small = cv2.resize(f_to_send, (640, 360))
                        _, buf = cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 55])
                        requests.post(
                            "http://localhost:5000/api/camera/frame",
                            data=buf.tobytes(),
                            headers={"Content-Type": "image/jpeg"},
                            timeout=0.35
                        )
                    except Exception:
                        pass
                import threading
                threading.Thread(target=_push_live_frame, args=(hud_frame.copy(),), daemon=True).start()

            # Render Professional Tactical HUD Window locally
            if not headless:
                cv2.imshow(window_name, hud_frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # 'q' or ESC
                    break

    except KeyboardInterrupt:
        print("\n[AI Engine] Streaming stopped by user (Ctrl+C).")
    finally:
        recorder.flush_and_save()
        backend.wait_for_pending_uploads(timeout=15)
        siren.stop()
        hardware.close()
        cap.release()
        if not headless:
            cv2.destroyAllWindows()
        print("[AI Engine] Surveillance engine shutdown completed cleanly.")


def main():
    parser = argparse.ArgumentParser(description="Smart Vehicle Theft Detection AI Engine")
    parser.add_argument("--source", default=VIDEO_SOURCE,
                        help="Camera index (e.g. 0), video file path, or phone IP stream URL "
                             "(e.g. http://192.168.1.5:8080/video for Android IP Webcam app, "
                             "or http://192.168.1.5:4747/video for DroidCam)")
    parser.add_argument("--sustained", type=float, default=SUSTAINED_SECONDS, help="Sustained occupancy threshold in seconds")
    parser.add_argument("--no-sound", action="store_true", help="Disable local siren sound")
    parser.add_argument("--headless", action="store_true", help="Run without opening GUI display window")
    args = parser.parse_args()

    src = args.source
    if isinstance(src, str) and src.isdigit():
        src = int(src)

    run_pipeline(
        source=src,
        sustained_sec=args.sustained,
        sound_on=not args.no_sound,
        headless=args.headless
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[AI Engine] Exited cleanly.")
        sys.exit(0)
