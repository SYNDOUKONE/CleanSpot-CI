import React, { useState } from "react";
import Scanner from "./components/Scanner.jsx";
import MapView from "./components/MapView.jsx";
import Dashboard from "./components/Dashboard.jsx";
import Review from "./components/Review.jsx";

const TABS = [
  { id: "scanner", label: "Scanner" },
  { id: "carte", label: "Carte" },
  { id: "dashboard", label: "Dashboard" },
  { id: "gestion", label: "Gestion" },
];

export default function App() {
  const [tab, setTab] = useState("scanner");

  return (
    <>
      <header className="app-header">
        <h1>CleanSpot CI</h1>
        <span className="tagline">
          Détection intelligente des dépôts sauvages de déchets à Abidjan
        </span>
      </header>
      <nav className="tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={t.id === tab ? "active" : ""}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>
      <main className="content">
        {tab === "scanner" && <Scanner />}
        {tab === "carte" && <MapView />}
        {tab === "dashboard" && <Dashboard />}
        {tab === "gestion" && <Review />}
      </main>
    </>
  );
}
