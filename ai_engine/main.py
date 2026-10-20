"""
ai_engine/main.py - Main entry point for Smart Vehicle Theft Detection AI Engine
"""
import argparse
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


def draw_hud(frame, sm_status, pixel_roi, detections, fps):
    """Renders a futuristic cyber-security HUD overlay on the camera feed."""
    h, w = frame.shape[:2]
    mode = sm_status['mode']
    state = sm_status['state']
    elapsed = sm_status['elapsed']
    threshold = sm_status['threshold']

    # 1. Determine ROI and Border Color
    if mode == SystemMode.DISARMED:
        roi_color = (160, 160, 160)  # Neutral Gray
        status_text = "SYSTEM: DISARMED [STANDBY]"
        status_bg = (50, 50, 50)
    elif state == DetectionState.CLEAR:
        roi_color = (0, 220, 0)      # Neon Green (Secure)
        status_text = "SYSTEM: ARMED [MONITORING CABIN]"
        status_bg = (0, 140, 0)
    elif state == DetectionState.ACCUMULATING:
        roi_color = (0, 180, 255)    # Amber/Yellow (Verifying Occupancy)
        progress = min(1.0, elapsed / max(0.1, threshold))
        status_text = f"VERIFYING OCCUPANT: {elapsed:.1f}s / {threshold:.1f}s ({int(progress * 100)}%)"
        status_bg = (0, 140, 220)
    elif state == DetectionState.ALARM_ACTIVE:
        # Flashing red/white alert
        flash = int(time.time() * 6) % 2 == 0
        roi_color = (0, 0, 255) if flash else (255, 255, 255)
        status_text = "CRITICAL: UNAUTHORIZED THEFT DETECTED!"
        status_bg = (0, 0, 200)
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
    cv2.putText(frame, "DRIVER CABIN ROI", (roi_top_center[0] - 60, max(20, roi_top_center[1])),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, roi_color, 1, cv2.LINE_AA)

    # 3. Draw Person Detections
    for det in detections:
        x1, y1, x2, y2 = det['bbox']
        conf = det['confidence']
        box_color = (0, 0, 255) if state in [DetectionState.ACCUMULATING, DetectionState.ALARM_ACTIVE] else (0, 255, 120)
        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
        label = f"Person {int(conf * 100)}%"
        cv2.putText(frame, label, (x1, max(15, y1 - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2, cv2.LINE_AA)

    # 4. Top Status Header Banner
    cv2.rectangle(frame, (0, 0), (w, 36), status_bg, -1)
    cv2.putText(frame, status_text, (15, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)

    # FPS counter on top right
    fps_label = f"FPS: {fps:.0f}"
    cv2.putText(frame, fps_label, (w - 90, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

    # 5. Progress Bar for Temporal Accumulation
    if state == DetectionState.ACCUMULATING:
        bar_w = int(w * 0.7)
        bar_h = 10
        bar_x = int((w - bar_w) / 2)
        bar_y = 44
        filled_w = int(bar_w * min(1.0, elapsed / threshold))
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (50, 50, 50), -1)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + filled_w, bar_y + bar_h), (0, 200, 255), -1)

    # 6. Bottom Navigation Bar
    cv2.rectangle(frame, (0, h - 28), (w, h), (25, 25, 25), -1)
    nav_text = "[A] Arm   [D] Disarm   [S] Silence Siren   [T] Test Alert   [Q] Quit"
    cv2.putText(frame, nav_text, (15, h - 9), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)

    return frame


def run_pipeline(source=VIDEO_SOURCE, sustained_sec=SUSTAINED_SECONDS, sound_on=SOUND_ENABLED, headless=False):
    """Main video capture, detection, and decision pipeline loop."""
    print("=" * 65)
    print("  SMART VEHICLE THEFT DETECTION - AI COMPUTER VISION ENGINE  ")
    print("=" * 65)
    print(f"  • Video Source     : {source}")
    print(f"  • Sustained Time   : {sustained_sec} seconds threshold")
    print(f"  • Sound Deterrent  : {'Enabled' if sound_on else 'Disabled'}")
    print("=" * 65)

    # Initialize modules
    detector = PersonDetector()
    state_machine = TheftStateMachine(sustained_seconds=sustained_sec)
    siren = AlarmSiren(enabled=sound_on)
    backend = BackendClient()

    # Open video capture
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[ERROR] Could not open video source: {source}")
        print("Tip: If you do not have a webcam attached, specify a test video: python -m ai_engine.main --source video.mp4")
        return

    prev_time = time.time()
    fps = 0.0

    window_name = "Smart Vehicle Security - Driver Seat Monitor"
    if not headless:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 800, 500)

    print("\n[AI Engine] Streaming started. Press 'Q' inside the camera window to exit.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                # If video file reached the end, loop back for continuous testing
                if isinstance(source, str):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                print("[AI Engine] Failed to read frame from camera.")
                break

            now = time.time()
            fps = 1.0 / max(0.001, (now - prev_time))
            prev_time = now

            # Get pixel coordinates for the driver seat ROI
            pixel_roi = detector.get_pixel_roi(frame.shape, DEFAULT_ROI_POLYGON)

            # 1. Detect Persons
            detections = detector.detect(frame)

            # 2. Check if any detected person occupies the driver seat ROI
            person_in_roi = False
            top_conf = 0.0
            for det in detections:
                if detector.is_in_roi(det, pixel_roi):
                    person_in_roi = True
                    top_conf = max(top_conf, det['confidence'])

            # 3. Update Theft State Machine
            sm_status = state_machine.update(person_in_roi, confidence=top_conf)

            # 4. Trigger Alarm if sustained threshold reached
            if sm_status['trigger_alarm_now']:
                print("\n" + "!" * 60)
                print(">>> [SECURITY ALERT] SUSTAINED THEFT OCCUPANCY CONFIRMED! <<<")
                print(f"    Confidence: {sm_status['highest_confidence']:.2f} | Duration: {sm_status['elapsed']:.1f}s")
                print("!" * 60 + "\n")

                # Sound the local deterrent siren
                siren.start()

                # Save evidence snapshot
                annotated_evidence = frame.copy()
                annotated_evidence = draw_hud(annotated_evidence, sm_status, pixel_roi, detections, fps)
                snapshot_file = backend.save_snapshot(annotated_evidence)

                # Dispatch incident to backend server
                backend.dispatch_incident_async(
                    snapshot_path=snapshot_file,
                    confidence=sm_status['highest_confidence'],
                    duration_seconds=sm_status['elapsed']
                )

            # 5. Render HUD and Display
            if not headless:
                hud_frame = draw_hud(frame.copy(), sm_status, pixel_roi, detections, fps)
                cv2.imshow(window_name, hud_frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # 'q' or ESC
                    break
                elif key == ord('a'):             # 'a' = ARM
                    state_machine.arm()
                elif key == ord('d'):             # 'd' = DISARM
                    state_machine.disarm()
                    siren.stop()
                elif key == ord('s'):             # 's' = SILENCE
                    siren.stop()
                    print("[AI Engine] Siren silenced.")
                elif key == ord('t'):             # 't' = TEST TRIGGER
                    print("[AI Engine] Manual test snapshot triggered.")
                    snapshot_file = backend.save_snapshot(frame, prefix="manual_test")
                    backend.dispatch_incident_async(snapshot_file, confidence=1.0, duration_seconds=0.0)

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

    # Convert numeric string to int for webcam index
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
