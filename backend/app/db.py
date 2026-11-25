from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.orm import Session

from .models import SessionLocal

__all__ = ["SessionLocal", "engine", "get_db", "init_db"]


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
