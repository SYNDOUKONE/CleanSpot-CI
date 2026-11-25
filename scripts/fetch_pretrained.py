#!/usr/bin/env python
"""Télécharge les poids COCO YOLOv8n (6 Mo) dans models/detection/yolov8n.pt.

Même sans entraînement, l'API fait alors de la vraie inférence via
CocoTrashDetector (bouteilles, gobelets/canettes, cartons — pas de sachets
ni d'amas, absents de COCO).

Usage : python scripts/fetch_pretrained.py
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import urllib.request
from pathlib import Path

URL = "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolov8n.pt"
DEST = Path(__file__).resolve().parent.parent / "models" / "detection" / "yolov8n.pt"


def main() -> int:
    if DEST.exists():
        print(f"Déjà présent : {DEST}")
        return 0
    DEST.parent.mkdir(parents=True, exist_ok=True)
    print(f"Téléchargement de {URL}...")
    with tempfile.NamedTemporaryFile() as tmp:
        urllib.request.urlretrieve(URL, tmp.name)
        shutil.move(tmp.name, DEST)
    print(f"Poids installés : {DEST} ({DEST.stat().st_size / 1e6:.1f} Mo)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
