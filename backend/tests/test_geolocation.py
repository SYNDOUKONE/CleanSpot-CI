from __future__ import annotations

import pytest

from app.geolocation import (
    accumulation_score,
    detect_hotspots,
    haversine_m,
    hotspot_status,
    merge_session_points,
)

# Une cinquantaine de mètres au nord d'Adjamé
BASE_LAT, BASE_LON = 5.3599, -4.0083


def obs(
    index: int,
    lat: float,
    lon: float,
    session_id: str = "s1",
    t: float = 1000.0,
    status: str = "confirmed",
    zone: str = "accumulation",
) -> dict:
    return {
        "id": index,
        "session_id": session_id,
        "captured_at": t,
        "latitude": lat,
        "longitude": lon,
        "zone_category": zone,
        "validation_status": status,
    }


def move(lat: float, meters_north: float) -> float:
    return lat + meters_north / 111320.0


def test_haversine_known_distance():
    distance = haversine_m(BASE_LAT, BASE_LON, move(BASE_LAT, 100), BASE_LON)
    assert 95 < distance < 105


def test_merge_session_bursts():
    burst = [obs(i, move(BASE_LAT, i * 2), BASE_LON, t=1000 + i * 5) for i in range(10)]
    merged = merge_session_points(burst)
    assert len(merged) == 1
    assert merged[0]["merged_count"] == 10


def test_merge_separates_distant_passes():
    far = [
        obs(10, move(BASE_LAT, 200), BASE_LON + 0.01, t=2000 + i)
        for i in range(3)
    ]
    near = [obs(i, BASE_LAT, BASE_LON, t=1000 + i * 5) for i in range(3)]
    merged = merge_session_points(near + far)
    assert len(merged) == 2


def test_detect_hotspots_clusters_and_orders():
    points = []
    idx = 0
    for session in ("s1", "s2", "s3"):
        t = 1000 * int(session[1])
        for i in range(4):
            points.append(
                obs(
                    idx,
                    move(BASE_LAT, i * 2),
                    BASE_LON,
                    session_id=session,
                    t=t + i * 5,
                    status="confirmed",
                )
            )
            idx += 1
    points.append(obs(idx, 6.8276, -5.2895, session_id="s4", t=500, status="confirmed"))

    hotspots = detect_hotspots(merge_session_points(points))
    assert len(hotspots) == 1
    top = hotspots[0]
    assert top["session_count"] == 3
    assert top["confirmed_count"] == 3
    assert top["status"] == "accumulation_to_verify"
    assert top["label"] == "Zone A"


def test_isolated_point_is_not_a_hotspot():
    points = [obs(0, BASE_LAT, BASE_LON, status="confirmed")]
    assert detect_hotspots(merge_session_points(points)) == []


def test_hotspot_status_thresholds():
    assert hotspot_status(1, 1, 1) == "isolated_observations"
    assert hotspot_status(4, 4, 2) == "accumulation_to_verify"
    assert hotspot_status(9, 9, 4) == "recurrent_accumulation"


def test_accumulation_score_rewards_recurrence():
    single_session = accumulation_score(10, 1)
    multi_session = accumulation_score(10, 4)
    assert multi_session > single_session
