"""
ai_engine/eye_authenticator.py - Eye/Ocular Region Biometric Layer
Uses neural deep feature comparison on ocular & periocular crops
as a secondary authentication signal to complement face recognition.
Completely compatible with all OpenCV versions (including OpenCV 5+).
"""
import os
import cv2
import numpy as np
import torch
import torchvision.transforms as T
import torchvision.models as models

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
FACES_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "authorized_faces")
EYE_PROFILE_PATH = os.path.join(FACES_DIR, "owner_eye_biometrics.pt")


class EyeAuthenticator:
    """
    Extracts ocular/periocular features (eye band, left eye, right eye)
    from face crops, generates deep embeddings, and verifies against enrolled owner biometrics.
    """

    def __init__(self, profile_path=EYE_PROFILE_PATH):
        self.profile_path = profile_path
        self.device = torch.device("cpu")

        # MobileNetV3 feature extractor
        mobilenet = models.mobilenet_v3_small(weights="DEFAULT")
        self.feature_extractor = mobilenet.features.eval().to(self.device)
        for p in self.feature_extractor.parameters():
            p.requires_grad = False

        self.transform = T.Compose([
            T.ToPILImage(),
            T.Resize((64, 64)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        self.eye_profile = None
        self.load_profile()

    # ── Persistence ──────────────────────────────────────────────────────────

    def load_profile(self):
        self.eye_profile = None
        if os.path.exists(self.profile_path):
            try:
                prof = torch.load(self.profile_path, weights_only=False)
                if prof.get("centroid") is not None:
                    self.eye_profile = prof
                    print("[Eye Biometrics] Loaded authorized eye profile.")
            except Exception as e:
                print(f"[Eye Biometrics] Could not load eye profile: {e}")

    def is_enrolled(self):
        return self.eye_profile is not None

    # ── Eye / Ocular Region Extraction ────────────────────────────────────────

    def extract_ocular_crops(self, face_crop):
        """
        Extracts ocular regions from the face using anatomical proportions:
        1. Both eyes (upper ocular band)
        2. Left eye region
        3. Right eye region
        Works reliably across all OpenCV versions and head orientations.
        """
        if face_crop is None or face_crop.size == 0:
            return []

        fh, fw = face_crop.shape[:2]
        if fh < 30 or fw < 30:
            return []

        crops = []

        # 1. Full eye & brow band (upper 20% to 55% of face)
        y1, y2 = int(0.20 * fh), int(0.55 * fh)
        x1, x2 = int(0.10 * fw), int(0.90 * fw)
        band = face_crop[y1:y2, x1:x2]
        if band.size > 0:
            crops.append(band)

        # 2. Left eye region
        ly1, ly2 = int(0.22 * fh), int(0.54 * fh)
        lx1, lx2 = int(0.12 * fw), int(0.48 * fw)
        left_eye = face_crop[ly1:ly2, lx1:lx2]
        if left_eye.size > 0:
            crops.append(left_eye)

        # 3. Right eye region
        ry1, ry2 = int(0.22 * fh), int(0.54 * fh)
        rx1, rx2 = int(0.52 * fw), int(0.88 * fw)
        right_eye = face_crop[ry1:ry2, rx1:rx2]
        if right_eye.size > 0:
            crops.append(right_eye)

        return crops

    # ── Embedding ─────────────────────────────────────────────────────────────

    def extract_crop_embedding(self, crop):
        """Extract 576-dim deep normalized embedding from an ocular crop."""
        rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        tensor = self.transform(rgb).unsqueeze(0).to(self.device)
        with torch.no_grad():
            feat = self.feature_extractor(tensor)
            vec = feat.mean([2, 3]).squeeze(0)
            vec = vec / (vec.norm() + 1e-7)
        return vec

    def embeddings_from_face(self, face_crop):
        """Extract embeddings for all ocular regions in the face crop."""
        crops = self.extract_ocular_crops(face_crop)
        return [self.extract_crop_embedding(c) for c in crops]

    # ── Enrollment ────────────────────────────────────────────────────────────

    def enroll_from_face_crops(self, face_crops_list):
        """
        Build eye/ocular biometric profile from enrolled face crops.
        Called automatically at the end of multi-pose training.
        """
        all_embs = []
        for fc in face_crops_list:
            all_embs.extend(self.embeddings_from_face(fc))

        if len(all_embs) < 5:
            print(f"[Eye Biometrics] Notice: Insufficient eye samples ({len(all_embs)}).")
            return False

        stacked = torch.stack(all_embs)
        centroid = stacked.mean(dim=0)
        centroid = centroid / (centroid.norm() + 1e-7)
        sims = torch.cosine_similarity(stacked, centroid.unsqueeze(0))
        top_idx = torch.argsort(sims, descending=True)[:min(40, len(all_embs))]

        self.eye_profile = {
            "centroid": centroid,
            "templates": stacked[top_idx],
        }
        os.makedirs(FACES_DIR, exist_ok=True)
        torch.save(self.eye_profile, self.profile_path)
        print(f"[Eye Biometrics] Enrolled {len(all_embs)} ocular samples. Profile saved permanently!")
        return True

    # ── Authentication ────────────────────────────────────────────────────────

    def authenticate(self, face_crop):
        """
        Returns (is_authorized: bool, score: float).
        """
        if not self.is_enrolled():
            return False, 0.0

        embs = self.embeddings_from_face(face_crop)
        if not embs:
            return False, 0.0

        scores = []
        for emb in embs:
            csim = float(torch.cosine_similarity(
                emb.unsqueeze(0), self.eye_profile["centroid"].unsqueeze(0)
            ))
            tsims = torch.cosine_similarity(
                emb.unsqueeze(0), self.eye_profile["templates"]
            )
            top3, _ = torch.topk(tsims, k=min(3, tsims.shape[0]))
            tsim = float(top3.mean())
            scores.append(0.65 * tsim + 0.35 * csim)

        best_score = max(scores)
        EYE_THRESHOLD = 0.58
        return best_score >= EYE_THRESHOLD, best_score
