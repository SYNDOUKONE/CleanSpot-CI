from __future__ import annotations

import base64
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import settings
from ..detection import (
    decode_image_bytes,
    draw_detections,
    encode_image_jpeg,
    load_detector,
)
from ..db import get_db
from ..schemas import (
    AnalyzeResponse,
    DetectionOut,
    ZoneAssessmentOut,
)
from ..storage import MediaStore
from ..zones import classify_zone
from .observations import create_observation

router = APIRouter(prefix="/api", tags=["analysis"])
_store = MediaStore()
_detector = None


def _ensure_detector():
    global _detector
    if _detector is None:
        _detector = load_detector(settings.detection_weights, settings.model_backend)
    return _detector


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_image(
    image: UploadFile = File(...),
    session_id: str = Form("adhoc"),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    commune: str | None = Form(None),
    captured_at: datetime | None = Form(None),
    annotate: bool = Form(False),
    save: bool = Form(True),
    db: Session = Depends(get_db),
):
    content = image.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Fichier image vide")

    try:
        image_rgb = decode_image_bytes(content)
    except Exception:
        raise HTTPException(status_code=400, detail="Image illisible")

    detector = _ensure_detector()
    detections = detector.predict(image_rgb)
    zone = classify_zone(detections)

    image_key = None
    if save and zone.category != "clean_zone":
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        image_key = f"{session_id}/{ts}.jpg"
        _store.save(image_key, encode_image_jpeg(image_rgb))

    observation_id = None
    if latitude is not None and longitude is not None:
        observation = create_observation(
            db,
            session_id=session_id,
            commune=commune,
            captured_at=captured_at or datetime.now(timezone.utc),
            latitude=latitude,
            longitude=longitude,
            zone=zone,
            image_key=image_key,
        )
        observation_id = observation.id

    annotated = None
    if annotate and detections:
        annotated = base64.b64encode(
            encode_image_jpeg(draw_detections(image_rgb, detections))
        ).decode()

    zone_out = ZoneAssessmentOut(
        category=zone.category,
        label=zone.label,
        detections_count=zone.detections_count,
        waste_area_ratio=zone.waste_area_ratio,
        class_counts=zone.class_counts,
        dominant_class=zone.dominant_class,
        needs_field_check=zone.needs_field_check,
    )

    return AnalyzeResponse(
        detections=[DetectionOut(**d.__dict__) for d in detections],
        zone=zone_out,
        observation_id=observation_id,
        image_key=image_key,
        model_backend=type(detector).__name__,
        annotated_image_base64=annotated,
    )

