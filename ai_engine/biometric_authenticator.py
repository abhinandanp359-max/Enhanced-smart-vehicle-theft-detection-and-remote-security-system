"""
ai_engine/biometric_authenticator.py - OpenCV YuNet + SFace Deep Learning Face Recognition
Combines YuNet facial landmark detection with SFace ArcFace/SphereFace 128-D face embeddings.
Provides mathematically robust, angle-invariant, and camera-invariant driver authentication.
"""
import os
import cv2
import numpy as np

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
FACES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "authorized_faces")
YUNET_PATH = os.path.join(MODELS_DIR, "face_detection_yunet_2023mar.onnx")
SFACE_PATH = os.path.join(MODELS_DIR, "face_recognition_sface_2021dec.onnx")
OWNER_PROFILE_PATH = os.path.join(FACES_DIR, "owner_sface_biometrics.npy")
OWNER_PHOTO_PATH = os.path.join(FACES_DIR, "owner_reference.jpg")

# Official OpenCV SFace matching threshold for Cosine Similarity:
# >= 0.363 means same identity in 1:1 match
SFACE_MATCH_THRESHOLD = 0.363

# High-Security Parameters for Anti-Theft Authentication:
# Dual-metric (Cosine + L2-Norm + Centroid + Consensus) prevents impostors while remaining stable over phone cameras.
HIGH_SEC_COSINE_THRESHOLD = 0.44     # High-security threshold tuned for both webcam and phone streams
HIGH_SEC_L2_THRESHOLD = 1.06         # Strict L2 Distance threshold (lower is closer; baseline is 1.128)
HIGH_SEC_CENTROID_THRESHOLD = 0.42   # Candidate face must correlate with owner identity centroid
HIGH_SEC_TOP3_THRESHOLD = 0.40       # Top-3 multi-angle templates must agree
REQUIRED_CONSECUTIVE_FRAMES = 2      # Fast 2-frame initial lock-on
GRACE_FRAMES_AFTER_AUTH = 12         # Absorbs Wi-Fi stream packet drops and momentary blinks (~0.6s)


class BiometricAuthenticator:
    def __init__(self, profile_path=OWNER_PROFILE_PATH):
        self.profile_path = profile_path

        # 1. Initialize YuNet Deep Face Detector
        if not os.path.exists(YUNET_PATH):
            import requests
            print("[Biometrics] Downloading YuNet Face Detector (232 KB)...")
            os.makedirs(MODELS_DIR, exist_ok=True)
            r = requests.get(
                "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
                allow_redirects=True, timeout=20
            )
            with open(YUNET_PATH, "wb") as f:
                f.write(r.content)
            print("[Biometrics] YuNet Face Detector downloaded.")

        self.face_detector = cv2.FaceDetectorYN.create(
            model=YUNET_PATH,
            config="",
            input_size=(640, 480),
            score_threshold=0.55,
            nms_threshold=0.3,
            top_k=5
        )

        # 2. Initialize SFace Deep Face Recognition Engine
        if not os.path.exists(SFACE_PATH):
            import urllib.request
            print("[Biometrics] Downloading SFace Face Recognizer (38 MB)...")
            os.makedirs(MODELS_DIR, exist_ok=True)
            urllib.request.urlretrieve(
                "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
                SFACE_PATH
            )
            print("[Biometrics] SFace Face Recognizer downloaded.")

        self.recognizer = cv2.FaceRecognizerSF.create(
            model=SFACE_PATH,
            config=""
        )

        # Cache for latest detection
        self.last_target_face = None
        self.last_embedding = None

        # Anti-flicker temporal hysteresis state
        self.consecutive_matches = 0
        self.is_currently_authorized = False
        self.grace_frames_left = 0

        self.enrolled_templates = []
        self.clean_templates = []
        self.centroid = None
        self.load_profile()

    def reset(self):
        """Immediately clears detection history and consecutive match counter when seat is vacant."""
        self.consecutive_matches = 0
        self.is_currently_authorized = False
        self.grace_frames_left = 0
        self.last_target_face = None
        self.last_embedding = None

    def load_profile(self):
        """Loads and pre-filters enrolled SFace owner templates into high-security centroid and clean sets."""
        self.enrolled_templates = []
        self.clean_templates = []
        self.centroid = None

        if os.path.exists(self.profile_path):
            try:
                data = np.load(self.profile_path, allow_pickle=True).item()
                raw_templates = data.get("templates", [])
                formatted = []
                for t in raw_templates:
                    if t is not None and t.size == 128:
                        emb = t.reshape(1, 128).astype(np.float32)
                        emb /= (np.linalg.norm(emb) + 1e-7)
                        formatted.append(emb)

                if formatted:
                    self.enrolled_templates = formatted
                    stacked = np.vstack(formatted)
                    mean_vec = np.mean(stacked, axis=0, keepdims=True).astype(np.float32)
                    mean_vec /= (np.linalg.norm(mean_vec) + 1e-7)
                    self.centroid = mean_vec

                    # Quality filter: remove blurry/noisy templates that deviate from identity centroid
                    filtered = []
                    for t in formatted:
                        sim = float(self.recognizer.match(t, self.centroid, cv2.FaceRecognizerSF_FR_COSINE))
                        if sim >= 0.44:
                            filtered.append(t)

                    self.clean_templates = filtered if len(filtered) >= 5 else formatted
                    print(f"[Biometrics] High-Security Profile Loaded: {len(self.clean_templates)} clean templates (from {len(formatted)} enrolled).")
            except Exception as e:
                print(f"[Biometrics] Error loading profile: {e}")
        else:
            print("[Biometrics] No SFace profile found. Run 'python -m ai_engine.train' to enroll.")

    def is_enrolled(self):
        return len(self.clean_templates) > 0 and self.centroid is not None

    def get_last_embedding(self):
        return self.last_embedding

    def find_face(self, frame, person_bbox=None):
        """
        Locates the exact face using YuNet inside the person bounding box.
        Extracts landmark-aligned SFace embedding if face is detected.
        Returns:
            face_crop: np.ndarray (RGB face crop) or None
            face_box: (fx, fy, fw, fh) pixel coordinates
            landmarks: list of (x, y) 5 facial landmark points
        """
        h, w = frame.shape[:2]
        self.face_detector.setInputSize((w, h))
        _, faces = self.face_detector.detect(frame)

        self.last_target_face = None
        self.last_embedding = None

        if faces is None or len(faces) == 0:
            if person_bbox is not None:
                px1, py1, px2, py2 = person_bbox
                bw = px2 - px1
                bh = py2 - py1
                fx = max(0, int(px1 + 0.20 * bw))
                fy = max(0, py1)
                fw = max(40, int(0.60 * bw))
                fh = max(40, int(0.35 * bh))
                crop = frame[fy:min(h, fy + fh), fx:min(w, fx + fw)]
                return crop, (fx, fy, fw, fh), []
            return None, (0, 0, 0, 0), []

        # Find the best face that falls within the person's bounding box
        target_face = None
        if person_bbox is not None:
            px1, py1, px2, py2 = person_bbox
            valid = []
            for f in faces:
                fcx, fcy = int(f[0] + f[2] / 2), int(f[1] + f[3] / 2)
                if px1 <= fcx <= px2 and py1 <= fcy <= py2:
                    valid.append(f)
            if valid:
                target_face = max(valid, key=lambda f: f[2] * f[3])
            else:
                target_face = max(faces, key=lambda f: f[2] * f[3])
        else:
            target_face = max(faces, key=lambda f: f[2] * f[3])

        self.last_target_face = target_face
        fx, fy, fw, fh = int(target_face[0]), int(target_face[1]), int(target_face[2]), int(target_face[3])

        # Extract 5 facial landmarks
        landmarks = []
        for i in range(4, 14, 2):
            landmarks.append((int(target_face[i]), int(target_face[i + 1])))

        # SFace landmark-guided affine alignment
        try:
            aligned = self.recognizer.alignCrop(frame, target_face)
            emb = self.recognizer.feature(aligned)
            if emb is not None and emb.size == 128:
                emb = emb.reshape(1, 128).astype(np.float32)
                emb /= (np.linalg.norm(emb) + 1e-7)
                self.last_embedding = emb
        except Exception:
            self.last_embedding = None

        # Face crop for display
        pad_x = int(0.12 * fw)
        pad_y = int(0.15 * fh)
        x1 = max(0, fx - pad_x)
        y1 = max(0, fy - pad_y)
        x2 = min(w, fx + fw + pad_x)
        y2 = min(h, fy + fh + pad_y)
        face_crop = frame[y1:y2, x1:x2]

        return face_crop, (fx, fy, fw, fh), landmarks

    def enroll_templates(self, embeddings_list, driver_name="Owner"):
        """Stores diverse multi-angle SFace embeddings permanently with centroid indexing."""
        if not embeddings_list:
            return False, "No face samples collected."

        cleaned = []
        for emb in embeddings_list:
            if emb is not None and emb.size == 128:
                norm_emb = emb.reshape(1, 128).astype(np.float32)
                norm_emb /= (np.linalg.norm(norm_emb) + 1e-7)
                cleaned.append(norm_emb)

        if not cleaned:
            return False, "No valid SFace embeddings found."

        self.enrolled_templates = cleaned
        stacked = np.vstack(cleaned)
        mean_vec = np.mean(stacked, axis=0, keepdims=True).astype(np.float32)
        mean_vec /= (np.linalg.norm(mean_vec) + 1e-7)
        self.centroid = mean_vec

        # Filter out outlier noise frames
        filtered = [t for t in cleaned if float(self.recognizer.match(t, self.centroid, cv2.FaceRecognizerSF_FR_COSINE)) >= 0.44]
        self.clean_templates = filtered if len(filtered) >= 5 else cleaned

        os.makedirs(FACES_DIR, exist_ok=True)
        data = {
            "name": driver_name,
            "templates": self.clean_templates,
            "centroid": self.centroid,
            "count": len(self.clean_templates)
        }
        np.save(self.profile_path, data)
        print(f"[Biometrics] High-Security Owner profile saved with {len(self.clean_templates)} clean templates to '{self.profile_path}'.")
        return True, f"Successfully trained Owner profile ({len(self.clean_templates)} clean templates)!"

    def enroll_samples(self, face_crops_list, driver_name="Owner"):
        """Compatibility fallback: saves reference photo."""
        if face_crops_list:
            os.makedirs(FACES_DIR, exist_ok=True)
            cv2.imwrite(OWNER_PHOTO_PATH, face_crops_list[0])
        return True, "Enrolled"

    def authenticate(self, frame, person_bbox):
        """
        High-Security Verification with Anti-Flicker Temporal Hysteresis.
        Returns:
            is_authorized: bool
            driver_name: str
            confidence_score: float (0.0 to 1.0)
            face_box: (fx, fy, fw, fh)
            landmarks: list of (x, y)
        """
        face_crop, face_box, landmarks = self.find_face(frame, person_bbox)

        if face_crop is None or face_box[2] < 20 or self.last_embedding is None:
            # Absorb momentary occlusion / looking away for authorized owner
            if self.is_currently_authorized and self.grace_frames_left > 0:
                self.grace_frames_left -= 1
                return True, "Authorized Owner", 0.90, face_box, landmarks
            self.is_currently_authorized = False
            self.consecutive_matches = 0
            return False, "Searching Face...", 0.0, face_box, landmarks

        if not self.is_enrolled():
            self.is_currently_authorized = False
            self.consecutive_matches = 0
            return False, "Unenrolled (Run Training)", 0.0, face_box, landmarks

        curr_emb = self.last_embedding

        # 1. Compare against clean enrolled pose templates
        cos_scores = [
            float(self.recognizer.match(tmpl, curr_emb, cv2.FaceRecognizerSF_FR_COSINE))
            for tmpl in self.clean_templates
        ]
        l2_scores = [
            float(self.recognizer.match(tmpl, curr_emb, cv2.FaceRecognizerSF_FR_NORM_L2))
            for tmpl in self.clean_templates
        ]

        best_cos = max(cos_scores) if cos_scores else 0.0
        best_l2 = min(l2_scores) if l2_scores else 999.0
        top3_cos = float(np.mean(sorted(cos_scores, reverse=True)[:min(3, len(cos_scores))])) if cos_scores else 0.0

        # 2. Compare against Core Owner Identity Centroid
        centroid_sim = float(self.recognizer.match(self.centroid, curr_emb, cv2.FaceRecognizerSF_FR_COSINE)) if self.centroid is not None else best_cos

        # 3. High-Security Verification Decision:
        is_frame_match = (
            best_cos >= HIGH_SEC_COSINE_THRESHOLD and
            best_l2 <= HIGH_SEC_L2_THRESHOLD and
            centroid_sim >= HIGH_SEC_CENTROID_THRESHOLD and
            top3_cos >= HIGH_SEC_TOP3_THRESHOLD
        )

        if is_frame_match:
            self.consecutive_matches += 1
            if self.consecutive_matches >= REQUIRED_CONSECUTIVE_FRAMES:
                self.is_currently_authorized = True
                self.grace_frames_left = GRACE_FRAMES_AFTER_AUTH
        else:
            self.consecutive_matches = 0
            if self.is_currently_authorized:
                self.grace_frames_left -= 1
                if self.grace_frames_left <= 0:
                    self.is_currently_authorized = False

        if self.is_currently_authorized:
            disp_conf = min(0.99, max(0.88, 0.75 + (best_cos - 0.40) * 0.7))
            return True, "Authorized Owner", disp_conf, face_box, landmarks

        # Unauthorized: compute accurate telemetry score
        raw_disp = min(0.40, max(0.05, best_cos * 0.6))
        return False, "Unauthorized Intruder", raw_disp, face_box, landmarks


