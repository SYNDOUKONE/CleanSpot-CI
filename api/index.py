"""Point d'entrée serverless Vercel : monte l'application FastAPI sur /api/*.

La base SQLite vit dans /tmp (éphémère) : c'est un mode démonstration.
Le stockage des images reste local /tmp, sauf si des variables S3/MinIO
sont configurées dans les variables d'environnement Vercel.
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402
