import React, { useEffect, useRef, useState } from "react";
import L from "leaflet";
import { listHotspots, listObservations, refreshHotspots } from "../api.js";

const COLORS = {
  recurrent_accumulation: "#d1452c",
  accumulation_to_verify: "#d97b2c",
  isolated_observations: "#d9a013",
  pending: "#d9a013",
  confirmed: "#0f9d58",
  rejected: "#9aa5a0",
};

function markerIcon(color) {
  return L.divIcon({
    className: "",
    html: `<span style="display:block;width:14px;height:14px;border-radius:50%;background:${color};border:2px solid #fff;box-shadow:0 0 3px rgba(0,0,0,.4)"></span>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

export default function MapView() {
  const mapRef = useRef(null);
  const [hotspots, setHotspots] = useState([]);
  const [observations, setObservations] = useState([]);
  const [message, setMessage] = useState(null);

  async function loadAll() {
    const [hs, obs] = await Promise.all([listHotspots(), listObservations({ limit: 300 })]);
    setHotspots(hs);
    setObservations(obs);
  }

  useEffect(() => {
    loadAll().catch((err) => setMessage(err.message));
  }, []);

  useEffect(() => {
    if (!mapRef.current) return;
    const map = L.map(mapRef.current, {
      center: [5.36, -4.06],
      zoom: 11,
      layers: [
        L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: "© OpenStreetMap",
        }),
      ],
    });

    observations.forEach((obs) => {
      if (obs.latitude == null) return;
      L.marker([obs.latitude, obs.longitude], {
        icon: markerIcon(COLORS[obs.validation_status] || "#999"),
      })
        .addTo(map)
        .bindPopup(
          `<b>${obs.zone_category}</b><br/>${obs.commune || "?"} · ${new Date(
            obs.captured_at
          ).toLocaleString("fr-FR")}<br/><small>${obs.validation_status}</small>`
        );
    });

    hotspots.forEach((hotspot) => {
      const color = COLORS[hotspot.status] || "#555";
      L.circle([hotspot.latitude, hotspot.longitude], {
        radius: 90 + hotspot.accumulation_score * 8,
        color,
        fillOpacity: 0.15,
      })
        .addTo(map)
        .bindPopup(
          `<b>${hotspot.label}</b><br/>${hotspot.status}<br/>` +
            `Signalements : ${hotspot.report_count} · Confirmés : ${hotspot.confirmed_count}` +
            `<br/>Score d'accumulation : ${hotspot.accumulation_score}`
        );
    });

    return () => map.remove();
  }, [hotspots, observations]);

  async function handleRefresh() {
    setMessage("Calcul des hotspots...");
    try {
      const hs = await refreshHotspots();
      setHotspots(hs);
      setMessage(`${hs.length} hotspot(s) calculé(s) via DBSCAN.`);
    } catch (err) {
      setMessage(err.message);
    }
  }

  return (
    <div className="card">
      <h2>Carte des signalements et zones d'accumulation</h2>
      <button className="secondary" onClick={handleRefresh}>
        Recalculer les hotspots (DBSCAN)
      </button>
      {message && <p>{message}</p>}
      <div ref={mapRef} className="map-container" />
      <div className="legend">
        <span>
          <span className="dot" style={{ background: "#0f9d58" }} /> Observations confirmées
        </span>
        <span>
          <span className="dot" style={{ background: "#d9a013" }} /> En attente / isolées
        </span>
        <span>
          <span className="dot" style={{ background: "#d97b2c" }} /> Accumulation à vérifier
        </span>
        <span>
          <span className="dot" style={{ background: "#d1452c" }} /> Accumulation récurrente
        </span>
      </div>
    </div>
  );
}
