#!/usr/bin/env python
"""Injecte des données de démonstration (observations géolocalisées + hotspots)
pour la démonstration devant le jury, sans modèle entraîné.

Usage : python scripts/seed_demo_data.py
"""
from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

random.seed(42)

CENTERS = {
    "Yopougon": (5.3376, -4.0866),
    "Abobo": (5.4296, -4.0214),
    "Adjamé": (5.3614, -4.0083),
}

from app.geolocation import detect_hotspots, merge_session_points
from app.models import Hotspot, Observation, SessionLocal, init_db

COMMUNES = list(CENTERS)


def jitter(base: tuple[float, float], meters: float) -> tuple[float, float]:
    lat, lon = base
    return (
        round(lat + random.uniform(-meters, meters) / 111320, 6),
        round(lon + random.uniform(-meters, meters) / 111320, 6),
    )


def main() -> int:
    init_db()
    db = SessionLocal()
    db.query(Observation).delete()
    db.query(Hotspot).delete()

    start = datetime.now(timezone.utc) - timedelta(days=14)
    observations: list[dict] = []
    index = 0
    for parcours in range(1, 13):
        commune = COMMUNES[parcours % len(COMMUNES)]
        center = CENTERS[commune]
        session_start = start + timedelta(days=parcours, hours=random.randint(6, 17))
        session_id = f"parcours-{commune.lower()}-{parcours:02d}"
        for photo in range(random.randint(8, 15)):
            index += 1
            lat, lon = jitter(center, random.choice([5, 15, 40, 90, 150, 400]))
            zone = random.choices(
                ["clean_zone", "isolated_waste", "accumulation", "suspect_deposit"],
                weights=[30, 30, 25, 15],
            )[0]
            lat = None if zone == "clean_zone" else lat
            lon = None if zone == "clean_zone" else lon
            captured_at = session_start + timedelta(seconds=photo * random.randint(20, 240))
            status = "confirmed" if zone in ("accumulation", "suspect_deposit") and random.random() < 0.8 else "pending"
            db.add(
                Observation(
                    session_id=session_id,
                    commune=commune,
                    captured_at=captured_at,
                    latitude=lat,
                    longitude=lon,
                    zone_category=zone,
                    detections_count=random.randint(0, 9),
                    class_counts=json.dumps({c: random.randint(0, 3) for c in [
                        "plastic_bottle", "plastic_bag", "metal_can",
                        "paper_cardboard", "mixed_waste"]}),
                    waste_area_ratio=round(random.uniform(0, 0.2), 3),
                    validation_status=status,
                )
            )

    db.commit()
    rows = [
        {
            "id": o.id,
            "session_id": o.session_id,
            "captured_at": o.captured_at.timestamp(),
            "latitude": o.latitude,
            "longitude": o.longitude,
            "zone_category": o.zone_category,
            "validation_status": o.validation_status,
        }
        for o in db.query(Observation).all()
    ]
    hotspots = detect_hotspots(merge_session_points(rows))
    for cluster in hotspots:
        db.add(
            Hotspot(
                label=cluster["label"],
                latitude=cluster["latitude"],
                longitude=cluster["longitude"],
                report_count=cluster["report_count"],
                confirmed_count=cluster["confirmed_count"],
                session_count=cluster["session_count"],
                accumulation_score=cluster["accumulation_score"],
                status=cluster["status"],
            )
        )
    db.commit()
    print(f"{len(rows)} observations et {len(hotspots)} hotspots injectés.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
