from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Hotspot, Observation
from ..schemas import StatsOut
from ..storage import parse_json_field

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count(Observation.id))) or 0
    pending = (
        db.scalar(
            select(func.count(Observation.id)).where(
                Observation.validation_status == "pending"
            )
        )
        or 0
    )
    confirmed = (
        db.scalar(
            select(func.count(Observation.id)).where(
                Observation.validation_status == "confirmed"
            )
        )
        or 0
    )
    rejected = (
        db.scalar(
            select(func.count(Observation.id)).where(
                Observation.validation_status == "rejected"
            )
        )
        or 0
    )
    hotspot_count = db.scalar(select(func.count(Hotspot.id))) or 0

    by_zone: dict[str, int] = {}
    by_commune: dict[str, int] = {}
    by_class: dict[str, int] = {}
    for obs in db.execute(select(Observation)).scalars().all():
        by_zone[obs.zone_category] = by_zone.get(obs.zone_category, 0) + 1
        if obs.commune:
            by_commune[obs.commune] = by_commune.get(obs.commune, 0) + 1
        for class_name, count in parse_json_field(obs.class_counts).items():
            by_class[class_name] = by_class.get(class_name, 0) + count

    return StatsOut(
        total_observations=total,
        pending_validations=pending,
        confirmed_count=confirmed,
        rejected_count=rejected,
        by_zone_category=by_zone,
        by_class=by_class,
        by_commune=by_commune,
        hotspot_count=hotspot_count,
    )
