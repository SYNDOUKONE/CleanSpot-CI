from __future__ import annotations

import base64
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
        classes = ["plastic_bottle", "plastic_bag", "metal_can", "paper_cardboard", "mixed_waste"]
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


def encode_image_jpeg(image: np.ndarray) -> bytes:
    import cv2

    ok, buf = cv2.imencode(".jpg", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    if not ok:
        raise ValueError("Encodage JPEG impossible")
    return buf.tobytes()


def draw_detections(image: np.ndarray, detections: list[Detection]) -> np.ndarray:
    import cv2

    out = image.copy()
    h, w = out.shape[:2]
    for det in detections:
        x1, y1, x2, y2 = det.bbox_xyxy_norm
        p1 = (int(x1 * w), int(y1 * h))
        p2 = (int(x2 * w), int(y2 * h))
        cv2.rectangle(out, p1, p2, (0, 200, 0), 2)
        cv2.putText(
            out,
            f"{det.class_name} {det.confidence:.2f}",
            (p1[0], max(12, p1[1] - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 200, 0),
            1,
            cv2.LINE_AA,
        )
    return out


def decode_data_url(data_url: str) -> np.ndarray:
    import cv2

    payload = data_url.split(",", 1)[-1]
    buf = np.frombuffer(base64.b64decode(payload), dtype=np.uint8)
    img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Image illisible")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
