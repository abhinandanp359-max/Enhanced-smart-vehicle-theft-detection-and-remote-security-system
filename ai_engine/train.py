"""
ai_engine/train.py - Multi-Pose Guided Owner Face Biometrics Training
Collects 150+ diverse face samples across 6 guided poses for angle-invariant recognition.
Poses: Front, Left, Right, Up, Down, Smile  (25 samples each)
"""
import time
import cv2
import numpy as np

from .config import VIDEO_SOURCE, DEFAULT_ROI_POLYGON
from .detector import PersonDetector
from .biometric_authenticator import BiometricAuthenticator
from .eye_authenticator import EyeAuthenticator

# ── Pose configuration ──────────────────────────────────────────────────────
POSES = [
    {"name": "LOOK STRAIGHT",  "hint": "Face camera directly — eyes level",      "samples": 25},
    {"name": "TURN LEFT",      "hint": "Slowly turn head to YOUR left (~30 deg)", "samples": 25},
    {"name": "TURN RIGHT",     "hint": "Slowly turn head to YOUR right (~30 deg)","samples": 25},
    {"name": "TILT UP",        "hint": "Chin up — look slightly upward",           "samples": 25},
    {"name": "TILT DOWN",      "hint": "Chin down — look slightly downward",       "samples": 25},
    {"name": "NATURAL SMILE",  "hint": "Face front and give a natural smile",      "samples": 25},
]

POSE_COLORS = [
    (0,  255, 120),   # Front   - green
    (0,  200, 255),   # Left    - cyan
    (255, 160,  0),   # Right   - amber
    (200, 100, 255),  # Up      - violet
    (80,  180, 255),  # Down    - sky
    (255, 220,  50),  # Smile   - gold
]


# ── Drawing helpers ──────────────────────────────────────────────────────────
def draw_corner_brackets(img, x, y, w, h, color, length=18, thickness=2):
    cv2.line(img, (x,     y),     (x + length, y),           color, thickness)
    cv2.line(img, (x,     y),     (x,     y + length),       color, thickness)
    cv2.line(img, (x + w, y),     (x + w - length, y),       color, thickness)
    cv2.line(img, (x + w, y),     (x + w, y + length),       color, thickness)
    cv2.line(img, (x,     y + h), (x + length, y + h),       color, thickness)
    cv2.line(img, (x,     y + h), (x,     y + h - length),   color, thickness)
    cv2.line(img, (x + w, y + h), (x + w - length, y + h),   color, thickness)
    cv2.line(img, (x + w, y + h), (x + w, y + h - length),   color, thickness)


def draw_hud_bar(frame, bx, by, bar_w, bar_h, progress, color):
    cv2.rectangle(frame, (bx - 2, by - 2), (bx + bar_w + 2, by + bar_h + 2), (30, 30, 30), -1)
    filled = int(bar_w * progress)
    cv2.rectangle(frame, (bx, by), (bx + filled, by + bar_h), color, -1)


def draw_overlay_panel(frame, h, w, pose_idx, pose, pose_color,
                       collected, total_so_far, total_target, elapsed_pose):
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h - 95), (w, h), (10, 10, 15), -1)
    cv2.addWeighted(overlay, 0.78, frame, 0.22, 0, frame)

    badge_txt = f"POSE {pose_idx + 1}/{len(POSES)}  |  {pose['name']}"
    cv2.putText(frame, badge_txt, (14, 32),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, pose_color, 2, cv2.LINE_AA)
    cv2.putText(frame, pose["hint"], (14, 56),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, (200, 200, 200), 1, cv2.LINE_AA)

    bar_w_px = int(w * 0.68)
    bx = int((w - bar_w_px) / 2)
    by = h - 66
    draw_hud_bar(frame, bx, by, bar_w_px, 12, min(1.0, collected / pose["samples"]), pose_color)
    cv2.putText(frame,
                f"POSE SAMPLES: {collected}/{pose['samples']}  ({int(min(1.0, collected/pose['samples'])*100)}%)",
                (bx, by - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.44, pose_color, 1, cv2.LINE_AA)

    by2 = h - 36
    draw_hud_bar(frame, bx, by2, bar_w_px, 10, min(1.0, total_so_far / total_target), (0, 220, 255))
    cv2.putText(frame,
                f"TOTAL ENROLMENT: {total_so_far}/{total_target}  ({int(min(1.0,total_so_far/total_target)*100)}%)",
                (bx, by2 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 220, 255), 1, cv2.LINE_AA)

    cv2.putText(frame, f"Pose time: {int(elapsed_pose)}s",
                (w - 155, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (160, 160, 160), 1, cv2.LINE_AA)


def show_pose_transition(cap, window_name, next_pose, pose_color, hold_secs=2.5):
    deadline = time.time() + hold_secs
    while time.time() < deadline:
        ret, frame = cap.read()
        if not ret:
            break
        h, w = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (5, 10, 20), -1)
        cv2.addWeighted(overlay, 0.72, frame, 0.28, 0, frame)

        remaining = max(0.0, deadline - time.time())
        cv2.putText(frame, "POSE COMPLETE!", (int(w * 0.28), int(h * 0.38)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.05, (0, 255, 120), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Next: {next_pose['name']}",
                    (int(w * 0.28), int(h * 0.50)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.80, pose_color, 2, cv2.LINE_AA)
        cv2.putText(frame, next_pose["hint"],
                    (int(w * 0.18), int(h * 0.61)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1, cv2.LINE_AA)
        cv2.putText(frame, f"Starting in {remaining:.1f}s ...",
                    (int(w * 0.30), int(h * 0.72)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 255), 1, cv2.LINE_AA)
        cv2.imshow(window_name, frame)
        cv2.waitKey(30)


# ── Main training pipeline ───────────────────────────────────────────────────
def run_training(source=VIDEO_SOURCE):
    total_target = sum(p["samples"] for p in POSES)

    print("=" * 68)
    print("   SMART VEHICLE SECURITY - MULTI-POSE OWNER BIOMETRIC TRAINING")
    print("=" * 68)
    print(f"  Collecting {total_target} samples across {len(POSES)} guided poses.")
    print("  Follow each on-screen instruction carefully.")
    print("=" * 68)

    detector      = PersonDetector()
    authenticator = BiometricAuthenticator()
    eye_auth      = EyeAuthenticator()

    src = source
    if isinstance(src, str) and src.isdigit():
        src = int(src)

    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print(f"[ERROR] Could not open camera source: {src}")
        return

    window_name = "Vehicle Security - Multi-Pose Owner Training"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 860, 560)

    all_crops       = []
    all_embeddings  = []
    pose_idx        = 0
    pose_start      = time.time()
    pose_crops      = []
    pose_embeddings = []

    # 3-second warm-up
    warmup_end = time.time() + 3.0
    while time.time() < warmup_end:
        ret, frame = cap.read()
        if not ret:
            break
        h, w = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
        remaining = max(0.0, warmup_end - time.time())
        cv2.putText(frame, "POSITION YOURSELF IN FRONT OF CAMERA",
                    (int(w * 0.08), int(h * 0.44)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.72, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Starting in {remaining:.1f}s ...",
                    (int(w * 0.30), int(h * 0.56)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.60, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.imshow(window_name, frame)
        cv2.waitKey(30)

    try:
        while pose_idx < len(POSES):
            pose       = POSES[pose_idx]
            pose_color = POSE_COLORS[pose_idx]

            ret, frame = cap.read()
            if not ret:
                break

            h, w      = frame.shape[:2]
            elapsed   = time.time() - pose_start
            pixel_roi = detector.get_pixel_roi(frame.shape, DEFAULT_ROI_POLYGON)

            cv2.polylines(frame, [pixel_roi], True, pose_color, 2)

            detections    = detector.detect(frame)
            target_person = None
            for det in detections:
                if detector.is_in_roi(det, pixel_roi):
                    target_person = det
                    break

            if target_person is not None:
                face_crop, face_box, landmarks = authenticator.find_face(frame, target_person["bbox"])
                if face_crop is not None and face_box[2] >= 35:
                    emb = authenticator.get_last_embedding()
                    if emb is not None:
                        pose_crops.append(face_crop)
                        pose_embeddings.append(emb)
                        fx, fy, fw, fh = face_box
                        draw_corner_brackets(frame, fx, fy, fw, fh, pose_color, length=16)
                        for lx, ly in landmarks:
                            cv2.circle(frame, (lx, ly), 3, (0, 255, 255), -1)
                        cv2.putText(frame, "CAPTURING...", (fx, max(18, fy - 10)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, pose_color, 2, cv2.LINE_AA)

            total_so_far = len(all_crops) + len(pose_crops)
            draw_overlay_panel(frame, h, w, pose_idx, pose, pose_color,
                               len(pose_crops), total_so_far, total_target, elapsed)

            cv2.imshow(window_name, frame)
            key = cv2.waitKey(30) & 0xFF
            if key in (27, ord('q')):
                print("[Training] Cancelled by user.")
                break

            # Pose complete
            if len(pose_crops) >= pose["samples"]:
                all_crops.extend(pose_crops)
                all_embeddings.extend(pose_embeddings)
                print(f"[Training] Pose '{pose['name']}' complete - {len(pose_crops)} samples.")
                pose_idx        += 1
                pose_crops       = []
                pose_embeddings  = []
                pose_start       = time.time()
                if pose_idx < len(POSES):
                    show_pose_transition(cap, window_name, POSES[pose_idx],
                                        POSE_COLORS[pose_idx], hold_secs=2.5)
                    pose_start = time.time()

        # Enrol
        if all_crops:
            print(f"\n[Biometrics] {len(all_embeddings)} SFace embeddings gathered! Building owner profile...")
            authenticator.enroll_templates(all_embeddings, driver_name="Owner")
            authenticator.enroll_samples(all_crops, driver_name="Owner")
            print("[Eye Biometrics] Enrolling eye biometrics from same samples...")
            eye_auth.enroll_from_face_crops(all_crops)

            ret, frame = cap.read()
            if ret:
                h, w = frame.shape[:2]
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, 0), (w, h), (0, 80, 20), -1)
                cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)
                cv2.putText(frame, "OWNER REGISTRATION COMPLETE!",
                            (int(w * 0.10), int(h * 0.43)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.95, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(frame, f"{len(all_crops)} multi-pose samples stored permanently.",
                            (int(w * 0.16), int(h * 0.54)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.58, (180, 255, 180), 1, cv2.LINE_AA)
                cv2.putText(frame, "Now run:  python -m ai_engine.main",
                            (int(w * 0.22), int(h * 0.64)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1, cv2.LINE_AA)
                cv2.imshow(window_name, frame)
                cv2.waitKey(3500)

    finally:
        cap.release()
        cv2.destroyAllWindows()

    print("\n" + "=" * 68)
    print(">>> SUCCESS: Multi-pose owner profile saved!             <<<")
    print(">>> Run:  python -m ai_engine.main                       <<<")
    print("=" * 68)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Multi-Pose Owner Face Training")
    parser.add_argument("--source", default=VIDEO_SOURCE,
                        help="Camera index (0,1,...) or IP stream URL "
                             "e.g. http://192.168.1.5:8080/video")
    args = parser.parse_args()
    run_training(source=args.source)
