#!/usr/bin/env python
"""Convertit les annotations COCO de TACO en format YOLO et replie les 28
super-catégories TACO vers les 5 classes CleanSpot CI.

Usage :
    python scripts/taco_to_yolo.py --taco-dir datasets/taco \
        --out-dir datasets/taco/yolo_cleanspot --split 80/10/10
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

CLASS_MAP = {
    # super-catégories TACO -> classes CleanSpot CI
    "bottle": "plastic_bottle",
    "plastic utensils": "plastic_bag",
    "cigarette": "mixed_waste",
    "pop tab": "metal_can",
    "carton": "paper_cardboard",
    "drink can": "metal_can",
    "other plastic": "mixed_waste",
    "paper": "paper_cardboard",
    "cardboard": "paper_cardboard",
}
FALLBACK_BY_NAME = {
    "metal": "metal_can",
    "paper": "paper_cardboard",
    "carton": "paper_cardboard",
    "bottle": "plastic_bottle",
    "plastic": "plastic_bag",
}
CLASSES = ["plastic_bottle", "plastic_bag", "metal_can", "paper_cardboard", "mixed_waste"]


def map_class(name: str) -> str | None:
    if name in CLASS_MAP:
        return CLASS_MAP[name]
    lowered = name.lower()
    for token, cls in FALLBACK_BY_NAME.items():
        if token in lowered:
            return cls
    return "mixed_waste"


def convert_split(ann_file: Path, images_root: Path, out_dir: Path, train_ratio: float) -> None:
    data = json.loads(ann_file.read_text())
    cats = {c["id"]: c["name"] for c in data["categories"]}
    images = {img["id"]: img for img in data["images"]}
    anns_by_image: dict[int, list[dict]] = {}
    for ann in data["annotations"]:
        anns_by_image.setdefault(ann["image_id"], []).append(ann)

    ids = sorted(images)
    random.shuffle(ids)
    n_train = int(len(ids) * train_ratio)

    for image_id in ids:
        image = images[image_id]
        anns = anns_by_image.get(image_id, [])
        if not anns:
            continue
        file_stem = Path(image["file_name"]).stem
        split = "train" if image_id in set(ids[:n_train]) else "val"
        labels_dir = out_dir / "labels" / split
        images_dir = out_dir / "images" / split
        labels_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)

        w, h = image["width"], image["height"]
        lines = []
        for ann in anns:
            x, y, bw, bh = ann["bbox"]
            cx, cy = (x + bw / 2) / w, (y + bh / 2) / h
            cls_name = map_class(cats[ann["category_id"]])
            lines.append(
                f"{CLASSES.index(cls_name)} {cx:.6f} {cy:.6f} {bw / w:.6f} {bh / h:.6f}"
            )
        (labels_dir / f"{file_stem}.txt").write_text("\n".join(lines))

    (out_dir / "dataset.yaml").write_text(
        f"path: {out_dir.resolve()}\n"
        "train: images/train\n"
        "val: images/val\n"
        f"names:\n" + "".join(f"  {i}: {name}\n" for i, name in enumerate(CLASSES))
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--taco-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    ann_file = args.taco_dir / "annotations.json"
    convert_split(ann_file, args.taco_dir, args.out_dir, train_ratio=0.8)
    print(f"Annotations YOLO écrites dans {args.out_dir}")
    return 0


if __name__ == "__main__":
    main()
