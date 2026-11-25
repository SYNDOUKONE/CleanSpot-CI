from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

WASTE_CLASSES = [
    "plastic_bottle",
    "plastic_bag",
    "metal_can",
    "paper_cardboard",
    "mixed_waste",
]

ZONE_CATEGORIES = ["clean_zone", "isolated_waste", "accumulation", "suspect_deposit"]
VALIDATION_STATUSES = ["pending", "confirmed", "rejected"]


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{BASE_DIR / 'cleanspot.db'}"
    detection_weights: Path = BASE_DIR.parent / "models" / "detection" / "best.pt"
    segmentation_weights: Path = BASE_DIR.parent / "models" / "segmentation" / "best-seg.pt"
    media_dir: Path = BASE_DIR / "media"
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
