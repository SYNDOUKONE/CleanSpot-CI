import React, { useEffect, useState } from "react";
import { fetchStats } from "../api.js";

const ZONE_LABELS = {
  clean_zone: "Zones propres",
  isolated_waste: "Déchets isolés",
  accumulation: "Accumulations",
  suspect_deposit: "Dépôts suspects",
};

const CLASS_LABELS = {
  plastic_bottle: "Bouteilles plastiques",
  plastic_bag: "Sachets plastiques",
  metal_can: "Canettes",
  paper_cardboard: "Papier / carton",
  mixed_waste: "Déchets mélangés",
};

function Bars({ title, data, labels }) {
  const entries = Object.entries(data).filter(([, v]) => v > 0);
  if (entries.length === 0) return null;
  const max = Math.max(...entries.map(([, v]) => v));
  return (
    <div className="card">
      <h2>{title}</h2>
      {entries.map(([key, value]) => (
        <div className="bar-row" key={key}>
          <span>{labels[key] || key}</span>
          <span className="bar" style={{ width: `${(value / max) * 100}%` }} />
          <span>{value}</span>
        </div>
      ))}
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStats().then(setStats).catch((err) => setError(err.message));
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!stats) return <p>Chargement...</p>;

  return (
    <>
      <div className="card">
        <h2>Vue d'ensemble</h2>
        <div className="bar-row">
          <span>Observations totales</span>
          <span className="bar" style={{ width: "45%", background: "#10291e" }} />
          <span>{stats.total_observations}</span>
        </div>
        <div className="bar-row">
          <span>En attente de validation</span>
          <span className="bar" style={{ width: "45%", background: "#d9a013" }} />
          <span>{stats.pending_validations}</span>
        </div>
        <div className="bar-row">
          <span>Confirmées</span>
          <span className="bar" style={{ width: "45%" }} />
          <span>{stats.confirmed_count}</span>
        </div>
        <div className="bar-row">
          <span>Rejetées</span>
          <span className="bar" style={{ width: "45%", background: "#9aa5a0" }} />
          <span>{stats.rejected_count}</span>
        </div>
        <div className="bar-row">
          <span>Hotspots identifiés</span>
          <span className="bar" style={{ width: "45%", background: "#d1452c" }} />
          <span>{stats.hotspot_count}</span>
        </div>
      </div>
      <Bars title="Observations par catégorie de zone" data={stats.by_zone_category} labels={ZONE_LABELS} />
      <Bars title="Nombre d'objets par classe de déchets" data={stats.by_class} labels={CLASS_LABELS} />
      <Bars title="Observations par commune" data={stats.by_commune} labels={{}} />
      <p>
        Taux de confirmations terrain :{" "}
        {stats.confirmed_count + stats.rejected_count > 0
          ? `${(
              (stats.confirmed_count / (stats.confirmed_count + stats.rejected_count)) *
              100
            ).toFixed(1)} % des signalements vérifiés`
          : "aucun signalement vérifié pour l'instant"}
      </p>
    </>
  );
}
