"""Dashboard d'analyse CleanSpot CI (Streamlit + Plotly).

Usage :
    pip install -r dashboard/requirements.txt
    streamlit run dashboard/app.py

L'API backend doit tourner sur http://localhost:8000.
"""
from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

API = os.getenv("CLEANSPOT_API", "http://localhost:8000")

ZONE_LABELS = {
    "clean_zone": "Zone propre",
    "isolated_waste": "Déchet isolé",
    "accumulation": "Accumulation",
    "suspect_deposit": "Dépôt suspect",
}

CLASS_LABELS = {
    "plastic_bottle": "Bouteilles plastiques",
    "plastic_bag": "Sachets plastiques",
    "metal_can": "Canettes",
    "paper_cardboard": "Papier / carton",
    "mixed_waste": "Déchets mélangés",
}

st.set_page_config(page_title="CleanSpot CI", layout="wide")
st.title("CleanSpot CI — Tableau de bord de salubrité")


@st.cache_data(ttl=30)
def get_json(path: str) -> dict:
    return requests.get(f"{API}{path}", timeout=10).json()


try:
    stats = get_json("/api/stats")
    hotspots = get_json("/api/hotspots")
    observations = get_json("/api/observations?limit=500")
except requests.exceptions.ConnectionError:
    st.error("API inaccessible. Démarrer le backend : uvicorn app.main:app --app-dir backend")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Observations", stats["total_observations"])
col2.metric("À valider", stats["pending_validations"])
col3.metric("Confirmées", stats["confirmed_count"])
col4.metric("Hotspots", stats["hotspot_count"])

left, right = st.columns(2)

if stats["by_zone_category"]:
    zones = pd.DataFrame(
        [
            {"Zone": ZONE_LABELS.get(k, k), "Observations": v}
            for k, v in stats["by_zone_category"].items()
        ]
    )
    left.plotly_chart(
        px.pie(
            zones,
            names="Zone",
            values="Observations",
            hole=0.4,
            title="Répartition des zones observées",
        ),
        use_container_width=True,
    )

if stats["by_class"]:
    classes = pd.DataFrame(
        [
            {"Classe": CLASS_LABELS.get(k, k), "Objets": v}
            for k, v in stats["by_class"].items()
        ]
    ).sort_values("Objets")
    right.plotly_chart(
        px.bar(
            classes,
            x="Objets",
            y="Classe",
            orientation="h",
            title="Objets détectés par classe de déchets",
        ),
        use_container_width=True,
    )

if stats["by_commune"]:
    communes = pd.DataFrame(
        [{"Commune": k, "Observations": v} for k, v in stats["by_commune"].items()]
    )
    st.plotly_chart(
        px.bar(communes, x="Commune", y="Observations", title="Observations par commune"),
        use_container_width=True,
    )

df = pd.DataFrame(observations)
if not df.empty:
    df["date"] = pd.to_datetime(df["captured_at"]).dt.date
    evolution = df.groupby(["date", "zone_category"]).size().reset_index(name="n")
    evolution["Zone"] = evolution["zone_category"].map(ZONE_LABELS)
    st.plotly_chart(
        px.line(
            evolution,
            x="date",
            y="n",
            color="Zone",
            title="Évolution des observations",
        ),
        use_container_width=True,
    )

hotspots_df = pd.DataFrame(hotspots)
if not hotspots_df.empty:
    st.subheader("Zones à inspecter en priorité")
    st.dataframe(
        hotspots_df[
            [
                "label",
                "status",
                "confirmed_count",
                "session_count",
                "accumulation_score",
                "latitude",
                "longitude",
            ]
        ],
        use_container_width=True,
    )
else:
    st.info("Aucun hotspot calculé — lancer POST /api/hotspots/refresh ou démarrer une collecte.")
