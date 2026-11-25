"""Segmentation des amas de déchets (YOLO-Seg / Mask R-CNN / U-Net).

Les poids segmentés ne sont pas requis pour faire tourner le prototype : en
leur absence, `load_segmenter` renvoie un segmenteur de repli qui produit un
masque plein cadre lorsque la zone est classée en accumulation. Cela permet de
tester le pipeline d'évaluation (IoU, Dice) et l'API sans entraînement.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .detection import BaseDetector, load_detector
from .zones import ZoneAssessment


class BaseSegmenter:
    def segment(self, image: np.ndarray) -> dict:
        raise NotImplementedError

    def available(self) -> bool:
        return False


class UltralyticsSegmenter(BaseSegmenter):
    def __init__(self, weights: Path):
        from ultralytics import YOLO

        self.model = YOLO(str(weights))
        self.names = self.model.names

    def segment(self, image: np.ndarray, conf: float = 0.25) -> dict:
        results = self.model.predict(image, conf=conf, verbose=False)
        out: list[dict] = []
        for result in results:
            if result.masks is None:
                continue
            for i, mask_tensor in enumerate(result.masks.data):
                mask = (
                    mask_tensor.cpu().numpy().astype(np.uint8)
                )
                cls_id = int(result.boxes.cls[i].item())
                out.append(
                    {
                        "class_name": self.names[cls_id],
                        "confidence": float(result.boxes.conf[i].item()),
                        "mask": mask,
                    }
                )
        return {"instances": out, "masks": [i["mask"] for i in out]}

    def available(self) -> bool:
        return True


class FallbackSegmenter(BaseSegmenter):
    """Produit un masque grossier à partir de la détection d'objets."""

    def __init__(self, detector: BaseDetector):
        self.detector = detector

    def segment(self, image: np.ndarray, conf: float = 0.25) -> dict:
        h, w = image.shape[:2]
        detections = self.detector.predict(image, conf=conf)
        mask = np.zeros((h, w), dtype=np.uint8)
        for det in detections:
            x1, y1, x2, y2 = det.bbox_xyxy_norm
            mask[int(y1 * h) : int(y2 * h), int(x1 * w) : int(x2 * w)] = 1
        return {"instances": [], "masks": [mask] if mask.any() else []}

    def available(self) -> bool:
        return False


def load_segmenter(weights: Path, detector: BaseDetector) -> BaseSegmenter:
    if Path(weights).exists():
        try:
            return UltralyticsSegmenter(weights)
        except Exception:
            pass
    return FallbackSegmenter(detector)


def segment_zone(
    segmenter: BaseSegmenter, image: np.ndarray, zone: ZoneAssessment
) -> dict:
    if zone.category == "clean_zone":
        return {"instances": [], "masks": [], "soiled_ratio": 0.0}
    result = segmenter.segment(image)
    masks = result.get("masks", [])
    if masks:
        soiled = min(1.0, float(sum(m.sum() for m in masks)) / masks[0].size)
    else:
        soiled = 0.0
    return {**result, "soiled_ratio": round(soiled, 4)}
