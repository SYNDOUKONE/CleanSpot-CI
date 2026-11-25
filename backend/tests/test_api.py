from __future__ import annotations

import io

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


def jpeg_bytes(w: int = 320, h: int = 240, seed: int = 0) -> bytes:
    rng = np.random.default_rng(seed)
    image = rng.integers(0, 255, size=(h, w, 3), dtype=np.uint8)
    buf = io.BytesIO()
    Image.fromarray(image).save(buf, format="JPEG")
    return buf.getvalue()


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_creates_geolocated_observation():
    response = client.post(
        "/api/analyze",
        files={"image": ("rue.jpg", io.BytesIO(jpeg_bytes(seed=1)), "image/jpeg")},
        data={
            "session_id": "parcours-yopougon-01",
            "latitude": "5.3376",
            "longitude": "-4.0866",
            "commune": "Yopougon",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["model_backend"] in {"MockDetector", "CocoTrashDetector", "UltralyticsDetector"}
    assert body["observation_id"] is not None
    assert body["zone"]["category"] in (
        "clean_zone",
        "isolated_waste",
        "accumulation",
        "suspect_deposit",
    )
    assert len(body["detections"]) == body["zone"]["detections_count"]

    listed = client.get(
        "/api/observations",
        params={"commune": "Yopougon", "session_id": "parcours-yopougon-01"},
    )
    assert listed.status_code == 200
    assert any(o["id"] == body["observation_id"] for o in listed.json())


def test_analyze_without_gps_still_returns_detections():
    response = client.post(
        "/api/analyze",
        files={"image": ("rue.jpg", io.BytesIO(jpeg_bytes(seed=2)), "image/jpeg")},
        data={"session_id": "adhoc"},
    )
    assert response.status_code == 200
    assert response.json()["observation_id"] is None


def test_analyze_rejects_invalid_image():
    response = client.post(
        "/api/analyze",
        files={"image": ("rue.jpg", io.BytesIO(b"not-an-image"), "image/jpeg")},
    )
    assert response.status_code == 400


def test_validate_observation():
    created = client.post(
        "/api/analyze",
        files={"image": ("rue.jpg", io.BytesIO(jpeg_bytes(seed=3)), "image/jpeg")},
        data={"latitude": "5.3376", "longitude": "-4.0866"},
    ).json()
    observation_id = created["observation_id"]
    validated = client.patch(
        f"/api/observations/{observation_id}/validate",
        json={"verdict": "confirmed", "agent": "agent-abidjan-01"},
    )
    assert validated.status_code == 200
    assert validated.json()["validation_status"] == "confirmed"
    assert validated.json()["validated_by"] == "agent-abidjan-01"


def test_hotspots_workflow():
    for i in range(5):
        client.post(
            "/api/analyze",
            files={
                "image": ("rue.jpg", io.BytesIO(jpeg_bytes(seed=10 + i)), "image/jpeg")
            },
            data={
                "session_id": f"session-{i % 2}",
                "latitude": str(5.36 + i * 0.0005),
                "longitude": "-4.01",
            },
        )
    refreshed = client.post("/api/hotspots/refresh")
    assert refreshed.status_code == 200
    listed = client.get("/api/hotspots")
    assert listed.status_code == 200
    for hotspot in listed.json():
        assert hotspot["status"] in (
            "isolated_observations",
            "accumulation_to_verify",
            "recurrent_accumulation",
        )


def test_stats_endpoint():
    stats = client.get("/api/stats")
    assert stats.status_code == 200
    body = stats.json()
    assert body["total_observations"] >= 1
    assert set(body) == {
        "total_observations",
        "pending_validations",
        "confirmed_count",
        "rejected_count",
        "by_zone_category",
        "by_class",
        "by_commune",
        "hotspot_count",
    }
