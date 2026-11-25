from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import VALIDATION_STATUSES, ZONE_CATEGORIES
from ..db import get_db
from ..models import Observation
from ..schemas import ObservationOut, ValidateRequest
from ..zones import ZoneAssessment

router = APIRouter(prefix="/api/observations", tags=["observations"])


def create_observation(
    db: Session,
    session_id: str,
    commune: str | None,
    captured_at: datetime,
    latitude: float | None,
    longitude: float | None,
    zone: ZoneAssessment,
    image_key: str | None,
) -> Observation:
    observation = Observation(
        session_id=session_id,
        commune=commune,
        captured_at=captured_at,
        latitude=latitude,
        longitude=longitude,
        zone_category=zone.category,
        detections_count=zone.detections_count,
        class_counts=json.dumps(zone.class_counts),
        waste_area_ratio=zone.waste_area_ratio,
        image_key=image_key,
        validation_status="pending",
    )
    db.add(observation)
    db.commit()
    db.refresh(observation)
    return observation


@router.get("", response_model=list[ObservationOut])
def list_observations(
    commune: str | None = Query(None),
    zone_category: str | None = Query(None),
    validation_status: str | None = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = select(Observation).order_by(Observation.captured_at.desc())
    if commune:
        query = query.where(Observation.commune == commune)
    if zone_category:
        if zone_category not in ZONE_CATEGORIES:
            raise HTTPException(400, f"Catégorie inconnue : {zone_category}")
        query = query.where(Observation.zone_category == zone_category)
    if validation_status:
        if validation_status not in VALIDATION_STATUSES:
            raise HTTPException(400, f"Statut inconnu : {validation_status}")
        query = query.where(Observation.validation_status == validation_status)
    rows = db.execute(query.offset(offset).limit(limit)).scalars().all()
    return [ObservationOut.from_model(o) for o in rows]


@router.patch("/{observation_id}/validate", response_model=ObservationOut)
def validate_observation(
    observation_id: int,
    payload: ValidateRequest,
    db: Session = Depends(get_db),
):
    observation = db.get(Observation, observation_id)
    if observation is None:
        raise HTTPException(404, "Observation introuvable")
    observation.validation_status = payload.verdict
    observation.validated_by = payload.agent
    db.commit()
    db.refresh(observation)
    return ObservationOut.from_model(observation)


@router.get("/{observation_id}", response_model=ObservationOut)
def get_observation(observation_id: int, db: Session = Depends(get_db)):
    observation = db.get(Observation, observation_id)
    if observation is None:
        raise HTTPException(404, "Observation introuvable")
    return ObservationOut.from_model(observation)
