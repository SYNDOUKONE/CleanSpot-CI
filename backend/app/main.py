from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models import init_db
from .routes import detections, hotspots, observations, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="CleanSpot CI API",
    description=(
        "Détection intelligente des dépôts sauvages de déchets à Abidjan : "
        "détection YOLO, classification de zone, géolocalisation et hotspots DBSCAN."
    ),
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(detections.router)
app.include_router(observations.router)
app.include_router(hotspots.router)
app.include_router(stats.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "cleanspot-ci", "version": "0.1.0"}
