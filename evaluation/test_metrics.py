from __future__ import annotations

import numpy as np

from metrics import (
    confirmations_report,
    dice,
    evaluate_by_route,
    iou,
    match_detections,
    precision_recall_f1,
)


def test_iou_identical_and_disjoint():
    box = (0, 0, 10, 10)
    assert iou(box, box) == 1.0
    assert iou(box, (20, 20, 30, 30)) == 0.0


def test_iou_partial():
    assert abs(iou((0, 0, 10, 10), (5, 0, 15, 10)) - 1 / 3) < 1e-6


def test_match_detections_counts():
    gt = [(0, 0, 10, 10), (20, 20, 30, 30)]
    pred = [(0, 0, 10, 10), (23, 23, 32, 32), (100, 100, 110, 110)]
    tp, fp, fn = match_detections(gt, pred, iou_threshold=0.5)
    assert (tp, fp, fn) == (1, 2, 1)


def test_precision_recall_f1():
    scores = precision_recall_f1(8, 2, 2)
    assert abs(scores["precision"] - 0.8) < 1e-9
    assert abs(scores["recall"] - 0.8) < 1e-9
    assert abs(scores["f1"] - 0.8) < 1e-9


def test_evaluate_by_route():
    routes = {"parcours-A": (8, 2, 2), "parcours-B": (6, 1, 4)}
    evaluated = evaluate_by_route(routes)
    assert set(evaluated) == {"parcours-A", "parcours-B"}
    assert evaluated["parcours-A"]["f1"] > 0


def test_dice_masks():
    gt = np.zeros((10, 10), dtype=np.uint8)
    pred = np.zeros((10, 10), dtype=np.uint8)
    gt[2:8, 2:8] = 1
    pred[2:8, 2:8] = 1
    assert dice(gt, pred) == 1.0
    pred[0, :] = 1
    assert dice(gt, pred) <= 0.87805


def test_confirmations_report():
    trips = [
        {"trip_id": "t1", "confirmed": True, "expected": True},
        {"trip_id": "t1", "confirmed": False, "expected": True},
        {"trip_id": "t2", "confirmed": False, "expected": False},
    ]
    report = confirmations_report(trips)
    assert abs(report["confirmation_rate"] - 1 / 3) < 1e-3
    assert report["false_reports_per_trip"] == 0.5
