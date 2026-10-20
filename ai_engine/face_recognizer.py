"""
ai_engine/face_recognizer.py - OpenCV YuNet + SFace Deep Learning Face Recognition
Differentiates between Authorized Owner/Driver and Unauthorized Intruder.
"""
import os
import cv2
import numpy as np
import requests

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
FACES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "authorized_faces")

YUNET_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
SFACE_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"

YUNET_PATH = os.path.join(MODELS_DIR, "face_detection_yunet_2023mar.onnx")
SFACE_PATH = os.path.join(MODELS_DIR, "face_recognition_sface_2021dec.onnx")
OWNER_PROFILE_PATH = os.path.join(FACES_DIR, "owner_embedding.npy")

# Official OpenCV SFace matching threshold for Cosine Similarity
COSINE_SIMILARITY_THRESHOLD = 0.363


def ensure_models_downloaded():
    """Download YuNet & SFace models if not present."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(FACES_DIR, exist_ok=True)

    for name, path, url in [
        ("YuNet Face Detector", YUNET_PATH, YUNET_URL),
        ("SFace Recognizer", SFACE_PATH, SFACE_URL)
    ]:
        if not os.path.exists(path) or os.path.getsize(path) < 100000:
            print(f"[Face Recognizer] Downloading {name} ({os.path.basename(path)})...")
            res = requests.get(url, allow_redirects=True, stream=True, timeout=60)
            res.raise_for_status()
            with open(path, "wb") as f:
                for chunk in res.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
            print(f"[Face Recognizer] {name} downloaded ({os.path.getsize(path) / (1024*1024):.1f} MB).")


class FaceRecognitionEngine:
    def __init__(self):
        ensure_models_downloaded()

        # Initialize YuNet Face Detector
        self.detector = cv2.FaceDetectorYN.create(
            model=YUNET_PATH,
            config="",
            input_size=(320, 320),
            score_threshold=0.6,
            nms_threshold=0.3,
            top_k=5
        )

        # Initialize SFace Face Recognizer
        self.recognizer = cv2.FaceRecognizerSF.create(
            model=SFACE_PATH,
            config=""
        )

        self.enrolled_embeddings = []
        self.load_enrolled_profiles()

    def load_enrolled_profiles(self):
        """Loads all authorized owner embeddings from authorized_faces/."""
        self.enrolled_embeddings = []
        if os.path.exists(OWNER_PROFILE_PATH):
            try:
                emb = np.load(OWNER_PROFILE_PATH)
                self.enrolled_embeddings.append({"name": "Owner", "embedding": emb})
                print(f"[Face Recognizer] Loaded authorized driver profile from '{OWNER_PROFILE_PATH}'.")
            except Exception as e:
                print(f"[Face Recognizer] Could not load profile: {e}")
        else:
            print("[Face Recognizer] Notice: No authorized face enrolled yet. (Press 'E' to enroll your face).")

    def enroll_face_from_frame(self, frame, name="Owner"):
        """Extracts face embedding from frame and saves as authorized driver."""
        h, w = frame.shape[:2]
        self.detector.setInputSize((w, h))
        _, faces = self.detector.detect(frame)

        if faces is None or len(faces) == 0:
            return False, "No face detected in frame. Please face the camera directly."

        # Pick the largest face (closest to camera)
        best_face = max(faces, key=lambda f: f[2] * f[3])
        aligned = self.recognizer.alignCrop(frame, best_face)
        embedding = self.recognizer.feature(aligned)

        # Save to disk
        os.makedirs(FACES_DIR, exist_ok=True)
        np.save(OWNER_PROFILE_PATH, embedding)
        self.enrolled_embeddings = [{"name": name, "embedding": embedding}]
        print(f"[Face Recognizer] Successfully enrolled '{name}' as Authorized Driver!")
        return True, f"Face enrolled successfully for {name}!"

    def identify_driver(self, frame, person_bbox=None):
        """
        Analyzes the driver's face in the frame.
        Returns:
            status: 'AUTHORIZED', 'UNAUTHORIZED', or 'NO_FACE_DETECTED'
            name: str ('Owner' or 'Intruder')
            score: float (cosine similarity score)
            face_box: (x, y, w, h) or None
        """
        h, w = frame.shape[:2]
        self.detector.setInputSize((w, h))
        _, faces = self.detector.detect(frame)

        if faces is None or len(faces) == 0:
            return 'NO_FACE_DETECTED', "Unknown", 0.0, None

        # If a person bounding box from YOLO is provided, find the face inside it
        if person_bbox is not None:
            px1, py1, px2, py2 = person_bbox
            valid_faces = []
            for f in faces:
                fx, fy, fw, fh = int(f[0]), int(f[1]), int(f[2]), int(f[3])
                fcx, fcy = fx + fw // 2, fy + fh // 2
                if px1 <= fcx <= px2 and py1 <= fcy <= py2:
                    valid_faces.append(f)
            if valid_faces:
                target_face = max(valid_faces, key=lambda f: f[2] * f[3])
            else:
                target_face = max(faces, key=lambda f: f[2] * f[3])
        else:
            target_face = max(faces, key=lambda f: f[2] * f[3])

        face_box = (int(target_face[0]), int(target_face[1]), int(target_face[2]), int(target_face[3]))

        # If no profile is enrolled yet, default to unauthorized until enrolled
        if not self.enrolled_embeddings:
            return 'UNAUTHORIZED', "Unenrolled Intruder", 0.0, face_box

        # Extract embedding and match against enrolled profiles
        aligned = self.recognizer.alignCrop(frame, target_face)
        curr_embedding = self.recognizer.feature(aligned)

        best_score = -1.0
        best_name = None

        for prof in self.enrolled_embeddings:
            score = self.recognizer.match(prof["embedding"], curr_embedding, cv2.FaceRecognizerSF_FR_COSINE)
            if score > best_score:
                best_score = score
                best_name = prof["name"]

        if best_score >= COSINE_SIMILARITY_THRESHOLD:
            return 'AUTHORIZED', best_name, float(best_score), face_box
        else:
            return 'UNAUTHORIZED', "Unauthorized Intruder", float(best_score), face_box
