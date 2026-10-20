"""
ai_engine/main.py - Main entry point for Smart Vehicle Theft Detection AI Engine
Includes Authorized Driver vs Unauthorized Intruder Verification & Emergency Deterrent Siren.
"""
import argparse
import os
import sys
import time
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
from .driver_authenticator import DriverAuthenticator


def draw_hud(frame, sm_status, pixel_roi, detections, head_bbox=None, fps=0.0, notification=""):
    """Renders a futuristic cyber-security HUD overlay on the camera feed."""
    h, w = frame.shape[:2]
    mode = sm_status['mode']
    state = sm_status['state']
    elapsed = sm_status['elapsed']
    threshold = sm_status['threshold']
    driver_name = sm_status.get('driver_name', 'Unknown')
    is_auth = sm_status.get('is_authorized', False)

    # 1. Determine ROI and Border Color
    if mode == SystemMode.DISARMED:
        roi_color = (150, 150, 150)  # Gray
        status_text = "SYSTEM: DISARMED [STANDBY]"
        status_bg = (50, 50, 50)
    elif state == DetectionState.CLEAR:
        roi_color = (0, 220, 0)      # Neon Green (Secure)
        status_text = "SYSTEM: ARMED [MONITORING DRIVER CABIN]"
        status_bg = (0, 140, 0)
    elif state == DetectionState.AUTHORIZED_DRIVER:
        roi_color = (0, 255, 120)    # Vibrant Emerald Green
        status_text = f"ACCESS GRANTED: AUTHORIZED DRIVER [{driver_name.upper()}]"
        status_bg = (0, 160, 40)
    elif state == DetectionState.ACCUMULATING:
        roi_color = (0, 80, 255)     # Warning Orange-Red
        progress = min(1.0, elapsed / max(0.1, threshold))
        status_text = f"ALERT: UNAUTHORIZED INTRUDER [{elapsed:.1f}s / {threshold:.1f}s] ({int(progress * 100)}%)"
        status_bg = (0, 60, 220)
    elif state == DetectionState.ALARM_ACTIVE:
        flash = int(time.time() * 6) % 2 == 0
        roi_color = (0, 0, 255) if flash else (255, 255, 255)
        status_text = "CRITICAL THEFT ALERT: UNAUTHORIZED INTRUDER DETECTED!"
        status_bg = (0, 0, 220)
    else:  # COOLDOWN
        roi_color = (255, 120, 0)
        status_text = f"ALERT DISPATCHED [COOLDOWN: {int(threshold - elapsed)}s]"
        status_bg = (180, 80, 0)

    # 2. Draw Semi-Transparent ROI Overlay
    roi_overlay = frame.copy()
    cv2.fillPoly(roi_overlay, [pixel_roi], roi_color)
    cv2.addWeighted(roi_overlay, 0.12, frame, 0.88, 0, frame)
    cv2.polylines(frame, [pixel_roi], isClosed=True, color=roi_color, thickness=2)

    # Label on top edge of ROI
    roi_top_center = (int(np.mean(pixel_roi[:, 0])), int(np.min(pixel_roi[:, 1])) - 8)
    cv2.putText(frame, "DRIVER CABIN ROI", (roi_top_center[0] - 65, max(20, roi_top_center[1])),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, roi_color, 1, cv2.LINE_AA)

    # 3. Draw Person Detections & Head Identity Box
    for det in detections:
        x1, y1, x2, y2 = det['bbox']
        conf = det['confidence']
        box_color = (0, 255, 100) if is_auth else ((0, 0, 255) if state in [DetectionState.ACCUMULATING, DetectionState.ALARM_ACTIVE] else (0, 220, 255))
        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
        cv2.putText(frame, f"Person {int(conf * 100)}%", (x1, max(15, y1 - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2, cv2.LINE_AA)

    # Draw Biometric Head Identifier
    if head_bbox and head_bbox[2] > head_bbox[0]:
        hx1, hy1, hx2, hy2 = head_bbox
        head_color = (0, 255, 0) if is_auth else (0, 0, 255)
        cv2.rectangle(frame, (hx1, hy1), (hx2, hy2), head_color, 2)
        auth_tag = "[AUTHORIZED OWNER]" if is_auth else "[UNAUTHORIZED INTRUDER]"
        cv2.putText(frame, auth_tag, (hx1, max(20, hy1 - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, head_color, 2, cv2.LINE_AA)

    # 4. Top Status Header Banner
    cv2.rectangle(frame, (0, 0), (w, 38), status_bg, -1)
    cv2.putText(frame, status_text, (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2, cv2.LINE_AA)

    # FPS counter on top right
    fps_label = f"FPS: {fps:.0f}"
    cv2.putText(frame, fps_label, (w - 85, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1, cv2.LINE_AA)

    # 5. Progress Bar for Unauthorized Intruder Accumulation
    if state == DetectionState.ACCUMULATING:
        bar_w = int(w * 0.7)
        bar_h = 10
        bar_x = int((w - bar_w) / 2)
        bar_y = 44
        filled_w = int(bar_w * min(1.0, elapsed / threshold))
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (40, 40, 40), -1)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + filled_w, bar_y + bar_h), (0, 0, 255), -1)

    # 6. Temporary On-Screen Notification Banner
    if notification:
        cv2.rectangle(frame, (int(w * 0.15), h - 75), (int(w * 0.85), h - 40), (0, 180, 255), -1)
        cv2.putText(frame, notification, (int(w * 0.17), h - 52),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 0, 0), 2, cv2.LINE_AA)

    # 7. Bottom Navigation Bar
    cv2.rectangle(frame, (0, h - 30), (w, h), (20, 20, 20), -1)
    nav_text = "[E] Enroll Face   [R] Reset Face   [A] Arm   [D] Disarm   [S] Silence   [Q] Quit"
    cv2.putText(frame, nav_text, (10, h - 9), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (210, 210, 210), 1, cv2.LINE_AA)

    return frame


def run_pipeline(source=VIDEO_SOURCE, sustained_sec=SUSTAINED_SECONDS, sound_on=SOUND_ENABLED, headless=False):
    """Main video capture, detection, biometric verification, and decision pipeline loop."""
    print("=" * 68)
    print("  SMART VEHICLE THEFT DETECTION - AI VISION & BIOMETRIC ENGINE  ")
    print("=" * 68)
    print(f"  • Video Source     : {source}")
    print(f"  • Sustained Time   : {sustained_sec}s threshold for unauthorized intruder")
    print(f"  • Sound Deterrent  : {'Enabled' if sound_on else 'Disabled'}")
    print("=" * 68)

    # Initialize modules
    detector = PersonDetector()
    state_machine = TheftStateMachine(sustained_seconds=sustained_sec)
    siren = AlarmSiren(enabled=sound_on)
    backend = BackendClient()
    authenticator = DriverAuthenticator()

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[ERROR] Could not open video source: {source}")
        return

    prev_time = time.time()
    fps = 0.0
    notification_msg = ""
    notification_until = 0.0

    window_name = "Smart Vehicle Security - Driver Seat Monitor"
    if not headless:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 840, 520)

    print("\n[AI Engine] Vision pipeline active.")
    print("  -> Press 'E' while sitting in the driver seat to enroll your face as Authorized Driver.")
    print("  -> Press 'R' to reset enrolled face and test the Unauthorized Intruder siren alarm.")
    print("  -> Press 'Q' to quit.\n")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                if isinstance(source, str):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break

            now = time.time()
            fps = 1.0 / max(0.001, (now - prev_time))
            prev_time = now

            pixel_roi = detector.get_pixel_roi(frame.shape, DEFAULT_ROI_POLYGON)

            # 1. Detect Persons using YOLOv8
            detections = detector.detect(frame)

            # 2. Check if person occupies the Driver Seat ROI
            person_in_roi = False
            top_conf = 0.0
            target_person = None
            for det in detections:
                if detector.is_in_roi(det, pixel_roi):
                    person_in_roi = True
                    target_person = det
                    top_conf = max(top_conf, det['confidence'])

            # 3. Biometric Verification (Authorized vs Unauthorized)
            is_authorized = False
            driver_name = "Unauthorized Intruder"
            head_bbox = None

            if person_in_roi and target_person is not None:
                is_authorized, driver_name, auth_score, head_bbox = authenticator.authenticate(
                    frame, target_person['bbox']
                )

            # 4. Update Multi-Factor State Machine
            sm_status = state_machine.update(
                person_in_roi=person_in_roi,
                is_authorized=is_authorized,
                driver_name=driver_name,
                confidence=top_conf
            )

            # 5. Trigger Alarm only for UNAUTHORIZED Occupants
            if sm_status['trigger_alarm_now']:
                print("\n" + "!" * 65)
                print(">>> [SECURITY ALERT] UNAUTHORIZED INTRUDER CONFIRMED IN DRIVER SEAT! <<<")
                print(f"    Target: {driver_name} | Duration: {sm_status['elapsed']:.1f}s")
                print("!" * 65 + "\n")

                # Sound emergency deterrent siren
                siren.start()

                # Save high-resolution evidence snapshot
                annotated_evidence = frame.copy()
                annotated_evidence = draw_hud(annotated_evidence, sm_status, pixel_roi, detections, head_bbox, fps)
                snapshot_file = backend.save_snapshot(annotated_evidence, prefix="theft_intruder")

                # Dispatch incident to backend server
                backend.dispatch_incident_async(
                    snapshot_path=snapshot_file,
                    confidence=sm_status['highest_confidence'],
                    duration_seconds=sm_status['elapsed']
                )

            # 6. Render HUD and Process User Commands
            if not headless:
                current_notif = notification_msg if now < notification_until else ""
                hud_frame = draw_hud(frame.copy(), sm_status, pixel_roi, detections, head_bbox, fps, current_notif)
                cv2.imshow(window_name, hud_frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # 'q' or ESC
                    break
                elif key == ord('e'):             # 'e' = ENROLL FACE
                    if target_person is not None:
                        success, msg = authenticator.enroll_driver(frame, target_person['bbox'], driver_name="Owner")
                        notification_msg = msg
                        notification_until = now + 4.0
                    else:
                        notification_msg = "Please sit inside the Driver Seat ROI to enroll face."
                        notification_until = now + 3.0
                elif key == ord('r'):             # 'r' = RESET PROFILE (Test Intruder mode)
                    if os.path.exists(authenticator.profile_path):
                        os.remove(authenticator.profile_path)
                    authenticator.authorized_profiles = []
                    notification_msg = "Face profile reset! System now treats everyone as Unauthorized Intruder."
                    notification_until = now + 4.0
                    print("[AI Engine] Profile reset. Testing Intruder mode.")
                elif key == ord('a'):             # 'a' = ARM
                    state_machine.arm()
                elif key == ord('d'):             # 'd' = DISARM
                    state_machine.disarm()
                    siren.stop()
                elif key == ord('s'):             # 's' = SILENCE
                    siren.stop()
                    print("[AI Engine] Siren silenced.")

    except KeyboardInterrupt:
        print("\n[AI Engine] Streaming stopped by user (Ctrl+C).")
    finally:
        siren.stop()
        cap.release()
        if not headless:
            cv2.destroyAllWindows()
        print("[AI Engine] Shutdown completed cleanly.")


def main():
    parser = argparse.ArgumentParser(description="Smart Vehicle Theft Detection AI Engine")
    parser.add_argument("--source", default=VIDEO_SOURCE, help="Webcam index (e.g. 0) or path to video file")
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
