"""
ai_engine/driver_authenticator.py - Driver Identity Verification Engine
Differentiates between Authorized Owner/Driver and Unauthorized Intruder
using SIFT feature matching and spatial visual biometric profiling.
Requires zero external weight downloads; works 100% locally and offline.
"""
import os
import pickle
import time
import cv2
import numpy as np

PROFILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "authorized_faces")
PROFILE_PATH = os.path.join(PROFILE_DIR, "authorized_owner.pkl")


class DriverAuthenticator:
    def __init__(self, profile_path=PROFILE_PATH):
        self.profile_path = profile_path
        self.sift = cv2.SIFT_create(nfeatures=500)
        self.matcher = cv2.BFMatcher(cv2.NORM_L2)
        self.authorized_profiles = []
        self.load_profile()

    def load_profile(self):
        """Loads enrolled driver profile if it exists."""
        self.authorized_profiles = []
        if os.path.exists(self.profile_path):
            try:
                with open(self.profile_path, "rb") as f:
                    self.authorized_profiles = pickle.load(f)
                print(f"[Authenticator] Loaded authorized driver profile from '{self.profile_path}'.")
            except Exception as e:
                print(f"[Authenticator] Could not load profile: {e}")
        else:
            print("[Authenticator] No authorized profile found. Press 'E' in camera window to enroll your face.")

    @staticmethod
    def extract_head_region(frame, person_bbox):
        """Extracts the head/face region from a person bounding box."""
        x1, y1, x2, y2 = person_bbox
        h, w = frame.shape[:2]

        box_w = x2 - x1
        box_h = y2 - y1

        # Head region is roughly top 35% of person height, centered horizontally
        hx1 = max(0, int(x1 + 0.15 * box_w))
        hx2 = min(w, int(x2 - 0.15 * box_w))
        hy1 = max(0, y1)
        hy2 = min(h, int(y1 + 0.38 * box_h))

        if hx2 <= hx1 or hy2 <= hy1:
            return None, (0, 0, 0, 0)

        head_crop = frame[hy1:hy2, hx1:hx2]
        return head_crop, (hx1, hy1, hx2, hy2)

    def extract_features(self, head_crop):
        """Extracts SIFT keypoint descriptors and normalized spatial grid histograms."""
        if head_crop is None or head_crop.size == 0:
            return None, None

        gray = cv2.cvtColor(head_crop, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (160, 160))
        gray = cv2.equalizeHist(gray)

        # 1. SIFT Keypoint Descriptors
        kps, descriptors = self.sift.detectAndCompute(gray, None)

        # 2. 4x4 Grid Spatial Histogram
        grid_hist = []
        step = 40
        for r in range(0, 160, step):
            for c in range(0, 160, step):
                cell = gray[r:r+step, c:c+step]
                hist = cv2.calcHist([cell], [0], None, [16], [0, 256])
                cv2.normalize(hist, hist)
                grid_hist.extend(hist.flatten())

        return descriptors, np.array(grid_hist, dtype=np.float32)

    def enroll_driver(self, frame, person_bbox, driver_name="Owner"):
        """
        Enrolls the person currently in front of the camera as the Authorized Driver.
        Saves their biometric profile to disk.
        """
        head_crop, head_bbox = self.extract_head_region(frame, person_bbox)
        if head_crop is None:
            return False, "Could not extract clear driver head region."

        descriptors, grid_hist = self.extract_features(head_crop)
        if descriptors is None or len(descriptors) < 15:
            return False, "Not enough distinct facial features detected. Please face the camera directly in good light."

        profile_entry = {
            "name": driver_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "descriptors": descriptors,
            "grid_hist": grid_hist
        }

        os.makedirs(PROFILE_DIR, exist_ok=True)
        self.authorized_profiles = [profile_entry]
        with open(self.profile_path, "wb") as f:
            pickle.dump(self.authorized_profiles, f)

        print(f"[Authenticator] >>> SUCCESS: Enrolled '{driver_name}' as Authorized Driver! <<<")
        return True, f"Successfully enrolled {driver_name}!"

    def authenticate(self, frame, person_bbox):
        """
        Checks if the person in person_bbox matches the enrolled Authorized Driver.
        Returns:
            is_authorized: bool (True for Owner, False for Intruder)
            name: str ('Owner' or 'Unauthorized Intruder')
            confidence: float (0.0 to 1.0)
            head_bbox: (hx1, hy1, hx2, hy2)
        """
        head_crop, head_bbox = self.extract_head_region(frame, person_bbox)
        if head_crop is None:
            return False, "Unknown Person", 0.0, (0, 0, 0, 0)

        # If no profile enrolled yet, classify as unauthorized to prompt enrollment
        if not self.authorized_profiles:
            return False, "Unenrolled Intruder", 0.0, head_bbox

        curr_descriptors, curr_hist = self.extract_features(head_crop)
        if curr_descriptors is None or len(curr_descriptors) < 5:
            return False, "Face Obscured / Intruder", 0.0, head_bbox

        best_auth = False
        best_name = "Unauthorized Intruder"
        best_score = 0.0

        for profile in self.authorized_profiles:
            ref_des = profile["descriptors"]
            ref_hist = profile["grid_hist"]

            # 1. SIFT Feature Matching with Lowe's Ratio Test
            try:
                knn_matches = self.matcher.knnMatch(curr_descriptors, ref_des, k=2)
                good_matches = 0
                for match in knn_matches:
                    if len(match) == 2:
                        m, n = match
                        if m.distance < 0.75 * n.distance:
                            good_matches += 1
            except Exception:
                good_matches = 0

            # 2. Histogram Correlation
            hist_sim = cv2.compareHist(curr_hist, ref_hist, cv2.HISTCMP_CORREL)

            # Combined confidence score
            sift_confidence = min(1.0, good_matches / 25.0)
            combined_score = max(0.0, 0.65 * sift_confidence + 0.35 * max(0.0, hist_sim))

            # Threshold for authorized driver
            if good_matches >= 12 and combined_score >= 0.40:
                best_auth = True
                best_name = profile["name"]
                best_score = combined_score
                break
            else:
                best_score = max(best_score, combined_score)

        return best_auth, best_name, best_score, head_bbox
