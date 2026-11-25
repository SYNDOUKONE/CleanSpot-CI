from __future__ import annotations

import json
from datetime import datetime

from pydantic import BaseModel, Field


class DetectionOut(BaseModel):
    class_name: str
    confidence: float
    bbox_xyxy_norm: tuple[float, float, float, float]

    class Config:
        from_attributes = True


class ZoneAssessmentOut(BaseModel):
    category: str
    label: str
    detections_count: int
    waste_area_ratio: float
    class_counts: dict[str, int]
    dominant_class: str | None
    needs_field_check: bool


class AnalyzeResponse(BaseModel):
    detections: list[DetectionOut]
    zone: ZoneAssessmentOut
    observation_id: int | None = None
    image_key: str | None = None
    model_backend: str
    annotated_image_base64: str | None = None


class ObservationOut(BaseModel):
    id: int
    session_id: str
    commune: str | None
    captured_at: datetime
    latitude: float | None
    longitude: float | None
    zone_category: str
    detections_count: int
    class_counts: dict[str, int]
    waste_area_ratio: float
    image_key: str | None
    validation_status: str
    validated_by: str | None

    class Config:
        from_attributes = True

    @classmethod
    def from_model(cls, obs) -> "ObservationOut":
        counts = json.loads(obs.class_counts) if obs.class_counts else {}
        return cls(
            id=obs.id,
            session_id=obs.session_id,
            commune=obs.commune,
            captured_at=obs.captured_at,
            latitude=obs.latitude,
            longitude=obs.longitude,
            zone_category=obs.zone_category,
            detections_count=obs.detections_count,
            class_counts=counts,
            waste_area_ratio=obs.waste_area_ratio,
            image_key=obs.image_key,
            validation_status=obs.validation_status,
            validated_by=obs.validated_by,
        )


class HotspotOut(BaseModel):
    id: int | None
    label: str
    latitude: float
    longitude: float
    report_count: int
    confirmed_count: int
    session_count: int
    accumulation_score: float
    status: str
    commune: str | None = None


class ValidateRequest(BaseModel):
    verdict: str = Field(pattern="^(confirmed|rejected)$")
    agent: str | None = None


class StatsOut(BaseModel):
    total_observations: int
    pending_validations: int
    confirmed_count: int
    rejected_count: int
    by_zone_category: dict[str, int]
    by_class: dict[str, int]
    by_commune: dict[str, int]
    hotspot_count: int
