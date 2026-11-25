from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..geolocation import detect_hotspots, merge_session_points
from ..models import Hotspot, Observation
from ..schemas import HotspotOut

router = APIRouter(prefix="/api/hotspots", tags=["hotspots"])

ACCUMULATION_ZONES = ("accumulation", "suspect_deposit")


def _collect_observations(db: Session, confirmed_only: bool = False) -> list[dict]:
    query = (
        select(Observation)
        .where(
            Observation.latitude.is_not(None),
            Observation.longitude.is_not(None),
            Observation.zone_category.in_(ACCUMULATION_ZONES),
        )
        .order_by(Observation.captured_at.asc())
    )
    if confirmed_only:
        query = query.where(Observation.validation_status == "confirmed")
    return [
        {
            "id": o.id,
            "session_id": o.session_id,
            "captured_at": o.captured_at.timestamp(),
            "latitude": o.latitude,
            "longitude": o.longitude,
            "zone_category": o.zone_category,
            "validation_status": o.validation_status,
        }
        for o in db.execute(query).scalars().all()
    ]


@router.post("/refresh", response_model=list[HotspotOut])
def refresh_hotspots(db: Session = Depends(get_db)):
    merged = merge_session_points(_collect_observations(db))
    clusters = detect_hotspots(merged)

    db.query(Hotspot).delete()
    saved = []
    for cluster in clusters:
        hotspot = Hotspot(
            label=cluster["label"],
            latitude=cluster["latitude"],
            longitude=cluster["longitude"],
            report_count=cluster["report_count"],
            confirmed_count=cluster["confirmed_count"],
            session_count=cluster["session_count"],
            accumulation_score=cluster["accumulation_score"],
            status=cluster["status"],
            updated_at=datetime.now(timezone.utc),
        )
        db.add(hotspot)
        saved.append(hotspot)
    db.commit()
    for hotspot in saved:
        db.refresh(hotspot)
    return [
        HotspotOut(
            id=h.id,
            label=h.label,
            latitude=h.latitude,
            longitude=h.longitude,
            report_count=h.report_count,
            confirmed_count=h.confirmed_count,
            session_count=h.session_count,
            accumulation_score=h.accumulation_score,
            status=h.status,
            commune=h.commune,
        )
        for h in saved
    ]


@router.get("", response_model=list[HotspotOut])
def list_hotspots(db: Session = Depends(get_db)):
    rows = (
        db.execute(
            select(Hotspot).order_by(Hotspot.accumulation_score.desc())
        )
        .scalars()
        .all()
    )
    return [
        HotspotOut(
            id=h.id,
            label=h.label,
            latitude=h.latitude,
            longitude=h.longitude,
            report_count=h.report_count,
            confirmed_count=h.confirmed_count,
            session_count=h.session_count,
            accumulation_score=h.accumulation_score,
            status=h.status,
            commune=h.commune,
        )
        for h in rows
    ]
