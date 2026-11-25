import os
from pathlib import Path

from pydantic_settings import BaseSettings

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

ON_SERVERLESS = bool(
    os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
)

WASTE_CLASSES = [
    "plastic_bottle",
    "plastic_bag",
    "metal_can",
    "paper_cardboard",
    "mixed_waste",
]

ZONE_CATEGORIES = ["clean_zone", "isolated_waste", "accumulation", "suspect_deposit"]
VALIDATION_STATUSES = ["pending", "confirmed", "rejected"]

DEFAULT_DB = (
    "sqlite:////tmp/cleanspot.db"
    if ON_SERVERLESS
    else f"sqlite:///{REPO_ROOT / 'cleanspot.db'}"
)
DEFAULT_MEDIA = Path("/tmp/media") if ON_SERVERLESS else REPO_ROOT / "backend" / "media"


class Settings(BaseSettings):
    database_url: str = DEFAULT_DB
    detection_weights: Path = REPO_ROOT / "models" / "detection" / "best.pt"
    segmentation_weights: Path = REPO_ROOT / "models" / "segmentation" / "best-seg.pt"
    media_dir: Path = DEFAULT_MEDIA
    model_backend: str = "auto"

    s3_endpoint: str | None = None
    s3_bucket: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None

    session_merge_seconds: int = 180
    session_merge_radius_m: float = 30.0
    hotspot_eps_m: float = 75.0
    hotspot_min_samples: int = 3

    class Config:
        env_prefix = "CLEANSPOT_"
        env_file = ".env"


settings = Settings()
