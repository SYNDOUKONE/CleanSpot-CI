from __future__ import annotations

import numpy as np
import pytest

from app.detection import (
    COCO_TO_WASTE,
    COCO_WEIGHTS,
    CocoTrashDetector,
    MockDetector,
    load_detector,
)

has_coco_weights = COCO_WEIGHTS.exists()


def test_coco_mapping_covers_key_classes():
    assert COCO_TO_WASTE[39] == "plastic_bottle"
    assert COCO_TO_WASTE[41] == "metal_can"
    assert COCO_TO_WASTE[73] == "paper_cardboard"


def test_mock_backend_forces_mock():
    detector = load_detector("inexistant.pt", backend="mock")
    assert isinstance(detector, MockDetector)


@pytest.mark.skipif(not has_coco_weights, reason="poids yolov8n.pt vendus absents")
def test_coco_weights_load_and_run():
    detector = load_detector("inexistant.pt")
    assert isinstance(detector, CocoTrashDetector)
    image = np.zeros((320, 320, 3), dtype=np.uint8)
    detections = detector.predict(image)
    assert isinstance(detections, list)


@pytest.mark.skipif(not has_coco_weights, reason="poids yolov8n.pt vendus absents")
def test_trained_weights_take_precedence():
    detector = load_detector(COCO_WEIGHTS)
    assert type(detector).__name__ == "UltralyticsDetector"
