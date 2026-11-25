from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class Detection:
    class_name: str
    confidence: float
    bbox_xyxy_norm: tuple[float, float, float, float]

    @property
    def area_ratio(self) -> float:
        x1, y1, x2, y2 = self.bbox_xyxy_norm
        return max(0.0, x2 - x1) * max(0.0, y2 - y1)


class BaseDetector:
    """Interface commune : une image RGB (H, W, 3) -> liste de Detection."""

    def predict(self, image: np.ndarray, conf: float = 0.25) -> list[Detection]:
        raise NotImplementedError

    def available(self) -> bool:
        return False


class UltralyticsDetector(BaseDetector):
    """Modèle YOLO (YOLOv8n / YOLO11n) entraîné sur TACO + pLitterStreet + CleanSpot CI."""

    def __init__(self, weights: Path):
        from ultralytics import YOLO

        self.model = YOLO(str(weights))
        self.names = self.model.names

    def predict(self, image: np.ndarray, conf: float = 0.25) -> list[Detection]:
        results = self.model.predict(image, conf=conf, verbose=False)
        out: list[Detection] = []
        for result in results:
            h, w = result.orig_shape
            for box in result.boxes:
                cls_id = int(box.cls.item())
                x1, y1, x2, y2 = (float(v) for v in box.xyxy[0].tolist())
                out.append(
                    Detection(
                        class_name=self.names[cls_id],
                        confidence=float(box.conf.item()),
                        bbox_xyxy_norm=(x1 / w, y1 / h, x2 / w, y2 / h),
                    )
                )
        return out

    def available(self) -> bool:
        return True


class MockDetector(BaseDetector):
    """Détecteur de démonstration : rectangles synthétiques déterministes.

    Permet de faire tourner toute la chaîne (API, cartographie, dashboard) sans
    poids entraînés ni GPU. À remplacer par UltralyticsDetector après l'entraînement.
    """

    def predict(self, image: np.ndarray, conf: float = 0.25) -> list[Detection]:
        h, w = image.shape[:2]
        gray = float(image.mean())
        seed = int((gray * 1000 + w * 7 + h * 3) % (2**32))
        rng = np.random.default_rng(seed)
        n = int(rng.integers(0, 7))
        classes = [
            "plastic_bottle",
            "plastic_bag",
            "metal_can",
            "paper_cardboard",
            "mixed_waste",
        ]
        out = []
        for _ in range(n):
            cls = classes[int(rng.integers(0, len(classes)))]
            cx, cy = float(rng.uniform(0.15, 0.85)), float(rng.uniform(0.2, 0.85))
            bw, bh = float(rng.uniform(0.03, 0.12)), float(rng.uniform(0.03, 0.12))
            out.append(
                Detection(
                    class_name=cls,
                    confidence=float(rng.uniform(0.4, 0.95)),
                    bbox_xyxy_norm=(cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2),
                )
            )
        return out


def load_detector(weights: Path, backend: str = "auto") -> BaseDetector:
    try:
        if Path(weights).exists():
            detector = UltralyticsDetector(weights)
            if backend != "mock":
                return detector
    except Exception:
        pass
    return MockDetector()


def decode_image_bytes(content: bytes) -> np.ndarray:
    from PIL import Image

    pil = Image.open(io.BytesIO(content))
    return np.asarray(pil.convert("RGB"))


def encode_image_jpeg(image: np.ndarray, quality: int = 88) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.fromarray(image).save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def draw_detections(image: np.ndarray, detections: list[Detection]) -> np.ndarray:
    from PIL import Image, ImageDraw, ImageFont

    h, w = image.shape[:2]
    pil = Image.fromarray(image.copy())
    draw = ImageDraw.Draw(pil)
    try:
        font = ImageFont.load_default(size=14)
    except TypeError:
        font = ImageFont.load_default()
    for det in detections:
        x1, y1, x2, y2 = det.bbox_xyxy_norm
        box = [x1 * w, y1 * h, x2 * w, y2 * h]
        draw.rectangle(box, outline=(25, 170, 70), width=2)
        label = f"{det.class_name} {det.confidence:.2f}"
        draw.text((box[0] + 2, max(0, box[1] - 16)), label, fill=(25, 170, 70), font=font)
    return np.asarray(pil)


def decode_data_url(data_url: str) -> np.ndarray:
    payload = data_url.split(",", 1)[-1]
    return decode_image_bytes(base64.b64decode(payload))
