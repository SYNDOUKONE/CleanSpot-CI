"""Métriques d'évaluation CleanSpot CI : détection, segmentation, cartographie.

- Détection : Precision, Recall, F1, mAP@50, mAP@50-95 (rapportés par Ultralytics
  lors de `model.val()` ; ci-dessous : calcul de detprécision et rappel manuel).
- Segmentation : IoU et Dice.
- Cartographie : taux de confirmation, faux signalements par parcours, taux de
  détection des zones connues.

Important : évaluer par parcours / zone géographique séparés pour mesurer la
généralisation, jamais sur des images quasi identiques au train.
"""
from __future__ import annotations

import numpy as np


def iou(box_a: tuple[int, int, int, int], box_b: tuple[int, int, int, int]) -> float:
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_x = max(0, min(ax2, bx2) - max(ax1, bx1))
    inter_y = max(0, min(ay2, by2) - max(ay1, by1))
    inter = inter_x * inter_y
    if inter == 0:
        return 0.0
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / union


def dice(mask_gt: np.ndarray, mask_pred: np.ndarray) -> float:
    if mask_gt.ndim > 2:
        mask_gt = mask_gt.any(axis=0)
    if mask_pred.ndim > 2:
        mask_pred = mask_pred.any(axis=0)
    total = int(mask_gt.sum() + mask_pred.sum())
    if total == 0:
        return 1.0
    return 2 * int(np.logical_and(mask_gt, mask_pred).sum()) / total


def match_detections(
    gt_boxes: list[tuple[int, int, int, int]],
    pred_boxes: list[tuple[int, int, int, int]],
    iou_threshold: float = 0.5,
) -> tuple[int, int, int]:
    """Retourne (TP, FP, FN) à un seuil IoU donné."""
    matched_gt: set[int] = set()
    tp = 0
    for pred in pred_boxes:
        best, best_iou = -1, 0.0
        for gt_index, gt in enumerate(gt_boxes):
            if gt_index in matched_gt:
                continue
            score = iou(gt, pred)
            if score > best_iou:
                best, best_iou = gt_index, score
        if best >= 0 and best_iou >= iou_threshold:
            matched_gt.add(best)
            tp += 1
    fp = len(pred_boxes) - tp
    fn = len(gt_boxes) - len(matched_gt)
    return tp, fp, fn


def precision_recall_f1(tp: int, fp: int, fn: int) -> dict[str, float]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def evaluate_by_route(
    routes: dict[str, tuple[int, int, int]],
) -> dict[str, dict[str, float]]:
    """Agrège les TP/FP/FN par parcours pour un benchmark géographiquement séparé."""
    return {
        route: precision_recall_f1(tp, fp, fn)
        for route, (tp, fp, fn) in routes.items()
    }


def confirmations_report(trips: list[dict]) -> dict[str, float]:
    """Métriques cartographie.

    Chaque entrée : {'trip_id': str, 'confirmed': bool, 'expected': bool}.
    - `confirmed` : le signalement a été validé sur le terrain.
    - `expected`  : l'équipe savait déjà qu'il y avait un dépôt ici.
    """
    total = len(trips)
    if total == 0:
        return {"confirmation_rate": 0.0, "false_reports_per_trip": 0.0}
    confirmed = sum(1 for t in trips if t.get("confirmed"))
    false_reports = sum(
        1 for t in trips if not t.get("confirmed") and not t.get("expected")
    )
    trips_count = len({t.get("trip_id", "") for t in trips} - {""}) or 1
    return {
        "confirmation_rate": round(confirmed / total, 4),
        "false_reports_per_trip": round(false_reports / trips_count, 3),
    }
