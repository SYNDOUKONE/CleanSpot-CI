from __future__ import annotations

import numpy as np

from app.detection import Detection
from app.zones import classify_zone


def det(cls: str, area: float, conf: float = 0.8) -> Detection:
    side = float(np.sqrt(area))
    return Detection(
        class_name=cls,
        confidence=conf,
        bbox_xyxy_norm=(0.5 - side / 2, 0.5 - side / 2, 0.5 + side / 2, 0.5 + side / 2),
    )


def test_clean_zone():
    zone = classify_zone([])
    assert zone.category == "clean_zone"
    assert not zone.needs_field_check


def test_isolated_waste():
    zone = classify_zone([det("plastic_bottle", 0.005)])
    assert zone.category == "isolated_waste"
    assert zone.dominant_class == "plastic_bottle"


def test_isolated_waste_two_small_objects():
    zone = classify_zone([det("plastic_bag", 0.004), det("metal_can", 0.004)])
    assert zone.category == "isolated_waste"


def test_accumulation():
    dets = [det(cls, 0.01) for cls in ["plastic_bottle"] * 3]
    zone = classify_zone(dets)
    assert zone.category == "accumulation"
    assert zone.needs_field_check


def test_suspect_deposit_by_count():
    dets = [det("mixed_waste", 0.01) for _ in range(9)]
    zone = classify_zone(dets)
    assert zone.category == "suspect_deposit"


def test_suspect_deposit_by_area():
    zones = classify_zone([det("mixed_waste", 0.10), det("paper_cardboard", 0.10)])
    assert zones.category == "suspect_deposit"


def test_dominant_class_and_counts():
    zone = classify_zone(
        [det("plastic_bottle", 0.01), det("plastic_bottle", 0.01), det("metal_can", 0.01)]
    )
    assert zone.class_counts == {"plastic_bottle": 2, "metal_can": 1}
    assert zone.dominant_class == "plastic_bottle"
