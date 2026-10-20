"""
ai_engine/train.py - Dedicated Owner Face & Biometrics Training Script
Captures 30 high-quality frames of the owner to build a permanent biometric profile.
Zero confusing controls; runs automatically with a live visual progress bar.
"""
import time
import cv2
import numpy as np

from .config import VIDEO_SOURCE, DEFAULT_ROI_POLYGON
from .detector import PersonDetector
from .biometric_authenticator import BiometricAuthenticator


def run_training(source=VIDEO_SOURCE, target_samples=30):
    print("=" * 65)
    print("       SMART VEHICLE SECURITY - OWNER BIOMETRICS ENROLLMENT       ")
    print("=" * 65)
    print("  • Please look directly at the camera.")
    print("  • Turn your head slightly (left, right, smile) while capturing.")
    print(f"  • Collecting {target_samples} biometric samples...")
    print("=" * 65)

    detector = PersonDetector()
    authenticator = BiometricAuthenticator()

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[ERROR] Could not open camera source {source}")
        return

    collected_crops = []
    window_name = "Owner Enrollment - Driver Biometrics Training"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 720, 480)

    start_countdown = 3.0
    start_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            h, w = frame.shape[:2]
            elapsed = time.time() - start_time
            pixel_roi = detector.get_pixel_roi(frame.shape, DEFAULT_ROI_POLYGON)

            # Draw Guide Target ROI
            cv2.polylines(frame, [pixel_roi], True, (0, 255, 200), 2)
            cv2.putText(frame, "KEEP FACE INSIDE DRIVER ZONE", (pixel_roi[0][0] + 10, pixel_roi[0][1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 200), 1, cv2.LINE_AA)

            # Detect Person
            detections = detector.detect(frame)
            target_person = None
            for det in detections:
                if detector.is_in_roi(det, pixel_roi):
                    target_person = det
                    break

            # 1. Warm-up 3-second countdown before capturing begins
            if elapsed < start_countdown:
                remaining = int(start_countdown - elapsed) + 1
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

                msg = f"TRAINING STARTING IN {remaining} SECONDS..."
                cv2.putText(frame, msg, (int(w * 0.15), int(h * 0.5)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(frame, "Please position your face comfortably in front of the camera.",
                            (int(w * 0.12), int(h * 0.58)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

            else:
                # 2. Capture Phase
                if target_person is not None:
                    head_crop, head_bbox = authenticator.extract_head_crop(frame, target_person['bbox'])
                    if head_crop is not None:
                        collected_crops.append(head_crop)
                        # Highlight head box
                        hx1, hy1, hx2, hy2 = head_bbox
                        cv2.rectangle(frame, (hx1, hy1), (hx2, hy2), (0, 255, 0), 2)
                        cv2.putText(frame, "Capturing Face Sample...", (hx1, max(20, hy1 - 6)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA)

                # Draw Live Progress Bar
                progress = min(1.0, len(collected_crops) / target_samples)
                bar_w = int(w * 0.7)
                bar_h = 16
                bx = int((w - bar_w) / 2)
                by = h - 50

                cv2.rectangle(frame, (bx - 4, by - 4), (bx + bar_w + 4, by + bar_h + 4), (20, 20, 20), -1)
                cv2.rectangle(frame, (bx, by), (bx + int(bar_w * progress), by + bar_h), (0, 255, 120), -1)

                prog_text = f"TRAINING PROGRESS: {len(collected_crops)} / {target_samples} ({int(progress * 100)}%)"
                cv2.putText(frame, prog_text, (bx, by - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2, cv2.LINE_AA)

                if len(collected_crops) >= target_samples:
                    print("\n[Biometrics] 30 frames captured! Computing owner deep template...")
                    success, msg = authenticator.enroll_samples(collected_crops, driver_name="Owner")
                    
                    # Final success banner on screen
                    cv2.rectangle(frame, (0, int(h * 0.35)), (w, int(h * 0.65)), (0, 160, 40), -1)
                    cv2.putText(frame, "OWNER TRAINING COMPLETE!", (int(w * 0.18), int(h * 0.48)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 3, cv2.LINE_AA)
                    cv2.putText(frame, "You are now permanently recognized as Authorized Owner.",
                                (int(w * 0.14), int(h * 0.56)), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 2, cv2.LINE_AA)
                    cv2.imshow(window_name, frame)
                    cv2.waitKey(2500)
                    break

            cv2.imshow(window_name, frame)
            key = cv2.waitKey(30) & 0xFF
            if key == 27 or key == ord('q'):
                print("[Biometrics] Enrollment cancelled by user.")
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("\n" + "=" * 65)
        print(">>> TRAINING COMPLETE! You can now run: python -m ai_engine.main <<<")
        print("=" * 65)


if __name__ == "__main__":
    run_training()
