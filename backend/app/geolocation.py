from __future__ import annotations

import numpy as np
from sklearn.cluster import DBSCAN

from .config import settings

EARTH_RADIUS_M = 6371000.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = p2 - p1
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return float(2 * EARTH_RADIUS_M * np.arcsin(np.sqrt(a)))


def merge_session_points(
    observations: list[dict],
    time_window_s: int | None = None,
    radius_m: float | None = None,
) -> list[dict]:
    """Fusionne les photos d'un même passage : une rafale de photos prises à
    quelques secondes d'intervalle au même endroit ne compte que pour un
    signalement indépendant.

    Une observation = dict avec captured_at (epoch s), latitude, longitude,
    session_id, validation_status, zone_category, id.
    """
    time_window_s = time_window_s or settings.session_merge_seconds
    radius_m = radius_m or settings.session_merge_radius_m

    by_session: dict[str, list[dict]] = {}
    for obs in observations:
        by_session.setdefault(obs["session_id"], []).append(obs)

    representatives: list[dict] = []
    for session_obs in by_session.values():
        session_obs = sorted(session_obs, key=lambda o: o["captured_at"])
        current: list[dict] = []
        for obs in session_obs:
            if (
                current
                and obs["captured_at"] - current[-1]["captured_at"] > time_window_s
            ):
                representatives.append(_merge_group(current))
                current = []
            elif (
                current
                and _distance_group(current, obs) is not None
                and _distance_group(current, obs) > radius_m
            ):
                representatives.append(_merge_group(current))
                current = []
            current.append(obs)
        if current:
            representatives.append(_merge_group(current))
    return representatives


def _distance_group(group: list[dict], obs: dict) -> float | None:
    if obs["latitude"] is None or obs["longitude"] is None:
        return None
    if group[-1]["latitude"] is None or group[-1]["longitude"] is None:
        return None
    return haversine_m(
        group[-1]["latitude"], group[-1]["longitude"], obs["latitude"], obs["longitude"]
    )


def _merge_group(group: list[dict]) -> dict:
    reps = [o for o in group if o["latitude"] is not None]
    base = dict(group[0])
    base["merged_count"] = len(group)
    if reps:
        base["latitude"] = float(np.mean([o["latitude"] for o in reps]))
        base["longitude"] = float(np.mean([o["longitude"] for o in reps]))
        base["member_ids"] = [o["id"] for o in group]
    else:
        base["member_ids"] = [o["id"] for o in group]
    return base


def hotspot_status(
    report_count: int, confirmed_count: int, session_count: int
) -> str:
    if confirmed_count < settings.hotspot_min_samples:
        return "isolated_observations"
    if confirmed_count >= 8 or (session_count >= 3 and confirmed_count >= 6):
        return "recurrent_accumulation"
    return "accumulation_to_verify"


def accumulation_score(confirmed_count: int, session_count: int) -> float:
    return round(confirmed_count * (1 + 0.5 * max(0, session_count - 1)), 2)


def detect_hotspots(
    observations: list[dict],
    eps_m: float | None = None,
    min_samples: int | None = None,
) -> list[dict]:
    """Regroupe les signalements géolocalisés (DBSCAN, métrique haversine).

    - `observations` : points déjà fusionnés par session (voir merge_session_points).
    - Un hotspot ne compte des signalements confirmés que d'au moins deux sessions.
    """
    eps_m = eps_m or settings.hotspot_eps_m
    min_samples = min_samples or settings.hotspot_min_samples

    points = [
        o
        for o in observations
        if o["latitude"] is not None and o["longitude"] is not None
    ]
    if not points:
        return []

    coords = np.radians([[o["latitude"], o["longitude"]] for o in points])
    db = DBSCAN(
        eps=eps_m / EARTH_RADIUS_M,
        min_samples=min_samples,
        metric="haversine",
    ).fit(coords)
    labels = db.labels_

    hotspots = []
    for label in sorted(set(labels) - {-1}):
        members = [o for o, lab in zip(points, labels) if lab == label]
        lat = float(np.mean([o["latitude"] for o in members]))
        lon = float(np.mean([o["longitude"] for o in members]))
        session_ids = {o["session_id"] for o in members}
        confirmed = sum(
            1 for o in members if o.get("validation_status") == "confirmed"
        )
        statuses = {o.get("zone_category") for o in members}
        has_accumulation = bool(
            statuses & {"accumulation", "suspect_deposit"}
        )
        report_count = sum(o.get("merged_count", 1) for o in members)
        hotspots.append(
            {
                "latitude": lat,
                "longitude": lon,
                "report_count": report_count,
                "confirmed_count": confirmed,
                "session_count": len(session_ids),
                "accumulation_score": accumulation_score(
                    confirmed, len(session_ids)
                ),
                "status": hotspot_status(confirmed, confirmed, len(session_ids)),
                "has_accumulation_zone": has_accumulation,
                "member_observation_ids": [
                    i for o in members for i in o.get("member_ids", [o["id"]])
                ],
            }
        )

    hotspots.sort(key=lambda h: h["accumulation_score"], reverse=True)
    for rank, hotspot in enumerate(hotspots, start=1):
        hotspot["label"] = f"Zone {chr(64 + rank)}" if rank <= 26 else f"Zone {rank}"
    return hotspots
