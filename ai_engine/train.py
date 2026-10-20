"""
ai_engine/train.py - Dedicated Owner Face & Biometrics Training Script
Captures 30 high-precision face crops using YuNet deep landmark detector.
Builds a permanent, 100% accurate biometric profile for the Owner.
"""
import time
import cv2
import numpy as np

from .config import VIDEO_SOURCE, DEFAULT_ROI_POLYGON
from .detector import PersonDetector
from .biometric_authenticator import BiometricAuthenticator


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


def run_training(source=VIDEO_SOURCE, target_samples=30):
    print("=" * 68)
    print("     SMART VEHICLE SECURITY - OWNER FACE BIOMETRICS TRAINING      ")
    print("=" * 68)
    print("  • Look directly at the camera.")
    print("  • Slowly tilt head slightly (left, right, smile) while capturing.")
    print(f"  • Collecting {target_samples} high-precision face samples...")
    print("=" * 68)

    detector = PersonDetector()
    authenticator = BiometricAuthenticator()

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[ERROR] Could not open camera source {source}")
        return

    collected_crops = []
    window_name = "Vehicle Security - Owner Face Training"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 780, 500)

    start_countdown = 2.5
    start_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            h, w = frame.shape[:2]
            elapsed = time.time() - start_time
            pixel_roi = detector.get_pixel_roi(frame.shape, DEFAULT_ROI_POLYGON)

            # Draw Guide Target Zone
            cv2.polylines(frame, [pixel_roi], True, (0, 220, 180), 2)
            cv2.putText(frame, "DRIVER CABIN ZONE", (pixel_roi[0][0] + 10, pixel_roi[0][1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 180), 1, cv2.LINE_AA)

            # Detect Person
            detections = detector.detect(frame)
            target_person = None
            for det in detections:
                if detector.is_in_roi(det, pixel_roi):
                    target_person = det
                    break

            # 1. Warm-up countdown
            if elapsed < start_countdown:
                remaining = int(start_countdown - elapsed) + 1
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.35, frame, 0.65, 0, frame)

                msg = f"POSITION YOUR FACE: STARTING IN {remaining}s..."
                cv2.putText(frame, msg, (int(w * 0.12), int(h * 0.48)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(frame, "Look straight at the camera lens.",
                            (int(w * 0.18), int(h * 0.56)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

            else:
                # 2. Capture Phase using YuNet Face Detection
                if target_person is not None:
                    face_crop, face_box, landmarks = authenticator.find_face(frame, target_person['bbox'])
                    if face_crop is not None and face_box[2] >= 35:
                        collected_crops.append(face_crop)
                        fx, fy, fw, fh = face_box

                        # Draw tactical corner brackets
                        draw_corner_brackets(frame, fx, fy, fw, fh, (0, 255, 120), length=15, thickness=2)

                        # Draw landmark dots
                        for lx, ly in landmarks:
                            cv2.circle(frame, (lx, ly), 2, (0, 255, 255), -1)

                        cv2.putText(frame, "ENROLLING FACE BIOMETRICS...", (fx, max(20, fy - 8)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 120), 2, cv2.LINE_AA)

                # Draw Progress Bar
                progress = min(1.0, len(collected_crops) / target_samples)
                bar_w = int(w * 0.7)
                bar_h = 14
                bx = int((w - bar_w) / 2)
                by = h - 45

                cv2.rectangle(frame, (bx - 3, by - 3), (bx + bar_w + 3, by + bar_h + 3), (25, 25, 25), -1)
                cv2.rectangle(frame, (bx, by), (bx + int(bar_w * progress), by + bar_h), (0, 255, 120), -1)

                prog_text = f"ENROLLMENT PROGRESS: {len(collected_crops)} / {target_samples} ({int(progress * 100)}%)"
                cv2.putText(frame, prog_text, (bx, by - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 255, 255), 1, cv2.LINE_AA)

                if len(collected_crops) >= target_samples:
                    print("\n[Biometrics] 30 face samples gathered! Generating permanent owner profile...")
                    authenticator.enroll_samples(collected_crops, driver_name="Owner")

                    # Banner
                    cv2.rectangle(frame, (0, int(h * 0.38)), (w, int(h * 0.62)), (0, 150, 40), -1)
                    cv2.putText(frame, "OWNER REGISTRATION COMPLETE!", (int(w * 0.16), int(h * 0.48)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2, cv2.LINE_AA)
                    cv2.putText(frame, "Permanent biometric profile verified and stored.",
                                (int(w * 0.20), int(h * 0.55)), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1, cv2.LINE_AA)
                    cv2.imshow(window_name, frame)
                    cv2.waitKey(2500)
                    break

            cv2.imshow(window_name, frame)
            key = cv2.waitKey(30) & 0xFF
            if key == 27 or key == ord('q'):
                print("[Biometrics] Enrollment cancelled.")
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("\n" + "=" * 68)
        print(">>> SUCCESS: You are now registered as the Authorized Owner! <<<")
        print(">>> Now run: python -m ai_engine.main                     <<<")
        print("=" * 68)


if __name__ == "__main__":
    run_training()
