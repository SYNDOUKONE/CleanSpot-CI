from __future__ import annotations

import io
import json
from pathlib import Path

import numpy as np

from .config import settings


class MediaStore:
    """Stockage des images : local par défaut, MinIO/S3 si configuré."""

    def __init__(self) -> None:
        self._s3 = None
        if settings.s3_bucket and settings.s3_endpoint:
            import boto3

            self._s3 = boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
            )

    def save(self, key: str, data: bytes) -> str:
        if self._s3 is not None:
            self._s3.put_object(Bucket=settings.s3_bucket, Key=key, Body=data)
            return key
        path = Path(settings.media_dir) / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def save_from_array(self, key: str, image: np.ndarray) -> str:
        from .detection import encode_image_jpeg

        buf = io.BytesIO(encode_image_jpeg(image))
        return self.save(key, buf.getvalue())


def parse_json_field(raw: str) -> dict:
    try:
        return json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {}
