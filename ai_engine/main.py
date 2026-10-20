"""
ai_engine/main.py - Smart Vehicle Theft Detection & Owner Verification Engine
Runs 100% automatically without requiring manual keyboard controls:
  1. Identifies the Authorized Owner (Neon Green, safe, silent).
  2. If an Unauthorized Intruder or stranger enters the driver seat:
     - Waits 3.0 seconds (temporal false-alarm filter).
     - Activates loud emergency deterrent siren.
     - Automatically captures and saves evidence photo.
     - Dispatches incident payload to backend server.
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
from .biometric_authenticator import BiometricAuthenticator


def draw_hud(frame, sm_status, pixel_roi, detections, head_bbox=None, fps=0.0):
    """Renders a futuristic cyber-security HUD overlay on the camera feed."""
    h, w = frame.shape[:2]
    mode = sm_status['mode']
    state = sm_status['state']
    elapsed = sm_status['elapsed']
    threshold = sm_status['threshold']
    driver_name = sm_status.get('driver_name', 'Unknown')
    is_auth = sm_status.get('is_authorized', False)

    # 1. Determine State Colors & Banner
    if state == DetectionState.CLEAR:
        roi_color = (0, 220, 0)      # Neon Green (Secure)
        status_text = "SYSTEM: ARMED [MONITORING CABIN - ALL SECURE]"
        status_bg = (0, 130, 0)
    elif state == DetectionState.AUTHORIZED_DRIVER:
        roi_color = (0, 255, 120)    # Emerald Green
        status_text = f"ACCESS GRANTED: AUTHORIZED OWNER [{driver_name.upper()}]"
        status_bg = (0, 150, 40)
    elif state == DetectionState.ACCUMULATING:
        roi_color = (0, 80, 255)     # Warning Amber-Red
        progress = min(1.0, elapsed / max(0.1, threshold))
        status_text = f"WARNING: UNAUTHORIZED INTRUDER [{elapsed:.1f}s / {threshold:.1f}s] ({int(progress * 100)}%)"
        status_bg = (0, 60, 210)
    elif state == DetectionState.ALARM_ACTIVE:
        flash = int(time.time() * 6) % 2 == 0
        roi_color = (0, 0, 255) if flash else (255, 255, 255)
        status_text = "CRITICAL THEFT: INTRUDER DETECTED! SIREN ACTIVE!"
        status_bg = (0, 0, 220)
    else:  # COOLDOWN
        roi_color = (255, 120, 0)
        status_text = f"THEFT ALERT RECORDED [COOLDOWN: {int(threshold - elapsed)}s]"
        status_bg = (180, 80, 0)

    # 2. Semi-Transparent Driver ROI Box
    roi_overlay = frame.copy()
    cv2.fillPoly(roi_overlay, [pixel_roi], roi_color)
    cv2.addWeighted(roi_overlay, 0.12, frame, 0.88, 0, frame)
    cv2.polylines(frame, [pixel_roi], isClosed=True, color=roi_color, thickness=2)

    roi_top_center = (int(np.mean(pixel_roi[:, 0])), int(np.min(pixel_roi[:, 1])) - 8)
    cv2.putText(frame, "DRIVER CABIN ZONE", (roi_top_center[0] - 65, max(20, roi_top_center[1])),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, roi_color, 1, cv2.LINE_AA)

    # 3. Person Detection & Biometric Identity Marking
    for det in detections:
        x1, y1, x2, y2 = det['bbox']
        conf = det['confidence']
        box_color = (0, 255, 100) if is_auth else ((0, 0, 255) if state in [DetectionState.ACCUMULATING, DetectionState.ALARM_ACTIVE] else (0, 220, 255))
        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
        cv2.putText(frame, f"Occupant {int(conf * 100)}%", (x1, max(15, y1 - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2, cv2.LINE_AA)

    if head_bbox and head_bbox[2] > head_bbox[0]:
        hx1, hy1, hx2, hy2 = head_bbox
        head_color = (0, 255, 0) if is_auth else (0, 0, 255)
        cv2.rectangle(frame, (hx1, hy1), (hx2, hy2), head_color, 2)
        auth_label = "AUTHORIZED OWNER" if is_auth else "UNAUTHORIZED INTRUDER"
        cv2.putText(frame, auth_label, (hx1, max(20, hy1 - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, head_color, 2, cv2.LINE_AA)

    # 4. Top Status Header
    cv2.rectangle(frame, (0, 0), (w, 38), status_bg, -1)
    cv2.putText(frame, status_text, (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2, cv2.LINE_AA)

    # FPS counter
    cv2.putText(frame, f"FPS: {fps:.0f}", (w - 85, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1, cv2.LINE_AA)

    # 5. Countdown Progress Bar for Unauthorized Intruder
    if state == DetectionState.ACCUMULATING:
        bar_w = int(w * 0.7)
        bar_h = 10
        bar_x = int((w - bar_w) / 2)
        bar_y = 44
        filled_w = int(bar_w * min(1.0, elapsed / threshold))
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (40, 40, 40), -1)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + filled_w, bar_y + bar_h), (0, 0, 255), -1)

    # 6. Bottom Information Bar
    cv2.rectangle(frame, (0, h - 28), (w, h), (20, 20, 20), -1)
    cv2.putText(frame, "Smart Vehicle Security Engine Active   |   Press 'Q' to quit",
                (15, h - 9), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 200, 200), 1, cv2.LINE_AA)

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

    if not authenticator.is_enrolled():
        print("\n" + "!" * 65)
        print(">>> NOTICE: No Owner Face Enrolled Yet! <<<")
        print("    Please run the training script first:")
        print("    -> python -m ai_engine.train")
        print("!" * 65 + "\n")

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[ERROR] Could not open video source: {source}")
        return

    prev_time = time.time()
    fps = 0.0

    window_name = "Smart Vehicle Security - Driver Seat Monitor"
    if not headless:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 840, 520)

    print("\n[AI Engine] Vision pipeline running automatically.")
    print("  -> Authorized Owner: Green, silent, safe.")
    print("  -> Unauthorized Intruder: Red, 3s countdown, then siren + auto-capture.")
    print("  -> Press 'Q' inside the camera window to exit.\n")

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

            # 2. Check if person is in the Driver Seat ROI
            person_in_roi = False
            top_conf = 0.0
            target_person = None
            for det in detections:
                if detector.is_in_roi(det, pixel_roi):
                    person_in_roi = True
                    target_person = det
                    top_conf = max(top_conf, det['confidence'])

            # 3. Biometric Verification (Owner vs Intruder)
            is_authorized = False
            driver_name = "Unauthorized Intruder"
            head_bbox = None

            if person_in_roi and target_person is not None:
                is_authorized, driver_name, auth_score, head_bbox = authenticator.authenticate(
                    frame, target_person['bbox']
                )

            # 4. Multi-Factor State Machine Decision
            sm_status = state_machine.update(
                person_in_roi=person_in_roi,
                is_authorized=is_authorized,
                driver_name=driver_name,
                confidence=top_conf
            )

            # If authorized owner is confirmed, ensure siren is stopped
            if is_authorized and siren.is_playing():
                siren.stop()

            # 5. Trigger Siren & Capture Evidence if Unauthorized Intruder stays >= 3.0s
            if sm_status['trigger_alarm_now']:
                print("\n" + "!" * 65)
                print(">>> [SECURITY ALERT] UNAUTHORIZED INTRUDER CONFIRMED IN DRIVER SEAT! <<<")
                print(f"    Target: {driver_name} | Duration: {sm_status['elapsed']:.1f}s")
                print("!" * 65 + "\n")

                # Sound emergency siren
                siren.start()

                # Automatically capture and save evidence snapshot
                annotated_evidence = frame.copy()
                annotated_evidence = draw_hud(annotated_evidence, sm_status, pixel_roi, detections, head_bbox, fps)
                snapshot_file = backend.save_snapshot(annotated_evidence, prefix="theft_intruder")
                print(f"[AI Engine] Evidence automatically captured & saved to: {snapshot_file}")

                # Automatically dispatch incident to backend server
                backend.dispatch_incident_async(
                    snapshot_path=snapshot_file,
                    confidence=sm_status['highest_confidence'],
                    duration_seconds=sm_status['elapsed']
                )

            # 6. Render HUD Window
            if not headless:
                hud_frame = draw_hud(frame.copy(), sm_status, pixel_roi, detections, head_bbox, fps)
                cv2.imshow(window_name, hud_frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # 'q' or ESC
                    break

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
