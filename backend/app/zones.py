from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import ZONE_CATEGORIES
from .detection import BaseDetector, Detection

ZONE_LABELS = {
    "clean_zone": "Zone propre",
    "isolated_waste": "Déchet isolé",
    "accumulation": "Accumulation",
    "suspect_deposit": "Dépôt suspect",
}

MIN_COUNT_FOR_SUSPECT = 8
MIN_AREA_FOR_SUSPECT = 0.14
MAX_AREA_FOR_ISOLATED = 0.02
MAX_COUNT_FOR_ISOLATED = 2


@dataclass(frozen=True)
class ZoneAssessment:
    category: str
    label: str
    detections_count: int
    waste_area_ratio: float
    class_counts: dict[str, int]
    dominant_class: str | None

    @property
    def needs_field_check(self) -> bool:
        return self.category in ("accumulation", "suspect_deposit")


def class_counts(detections: list[Detection]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for det in detections:
        counts[det.class_name] = counts.get(det.class_name, 0) + 1
    return counts


def classify_zone(detections: list[Detection]) -> ZoneAssessment:
    """Sépare la détection d'objets de l'appréciation de la zone.

    Un dépôt n'est jamais déclaré automatiquement : la catégorie
    `suspect_deposit` déclenche une vérification humaine, pas une constatation.
    """
    count = len(detections)
    area = float(sum(det.area_ratio for det in detections))
    counts = class_counts(detections)
    dominant = max(counts, key=counts.get) if counts else None

    if count == 0:
        category = "clean_zone"
    elif count <= MAX_COUNT_FOR_ISOLATED and area <= MAX_AREA_FOR_ISOLATED:
        category = "isolated_waste"
    elif count >= MIN_COUNT_FOR_SUSPECT or area >= MIN_AREA_FOR_SUSPECT:
        category = "suspect_deposit"
    else:
        category = "accumulation"

    return ZoneAssessment(
        category=category,
        label=ZONE_LABELS[category],
        detections_count=count,
        waste_area_ratio=round(area, 4),
        class_counts=counts,
        dominant_class=dominant,
    )


def assert_valid_zone(category: str) -> None:
    if category not in ZONE_CATEGORIES:
        raise ValueError(f"Catégorie de zone inconnue : {category}")


def mask_area_ratios(masks: list[np.ndarray]) -> float:
    """Somme des surfaces de masques de segmentation, en fraction de l'image."""
    if not masks:
        return 0.0
    total = 0.0
    for mask in masks:
        total += float(mask.sum())
    h, w = masks[0].shape
    return min(1.0, total / (h * w))
