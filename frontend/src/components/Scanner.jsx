import React, { useState } from "react";
import { analyzeImage } from "../api.js";

const ZONE_LABELS = {
  clean_zone: "Zone propre",
  isolated_waste: "Déchet isolé",
  accumulation: "Accumulation",
  suspect_deposit: "Dépôt suspect",
};

export default function Scanner() {
  const [file, setFile] = useState(null);
  const [commune, setCommune] = useState("Yopougon");
  const [useGps, setUseGps] = useState(true);
  const [sessionId, setSessionId] = useState(
    `parcours-${new Date().toISOString().slice(0, 10)}`
  );
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function getPosition() {
    if (!useGps || !navigator.geolocation) return {};
    return new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        (pos) =>
          resolve({ latitude: pos.coords.latitude, longitude: pos.coords.longitude }),
        () => resolve({})
      );
    });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!file) {
      setError("Choisir une photo d'abord.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const position = await getPosition();
      setResult(
        await analyzeImage(file, {
          sessionId,
          commune,
          annotate: true,
          ...position,
        })
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div className="card">
        <h2>Scanner une rue</h2>
        <form onSubmit={handleSubmit}>
          <p>
            <input
              type="file"
              accept="image/*"
              capture="environment"
              onChange={(e) => setFile(e.target.files[0])}
            />
          </p>
          <p>
            Session de collecte :{" "}
            <input
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
              size={28}
            />
          </p>
          <p>
            Commune :{" "}
            <select value={commune} onChange={(e) => setCommune(e.target.value)}>
              <option>Yopougon</option>
              <option>Abobo</option>
              <option>Adjamé</option>
              <option>Cocody</option>
              <option>Port-Bouët</option>
            </select>{" "}
            <label>
              <input
                type="checkbox"
                checked={useGps}
                onChange={(e) => setUseGps(e.target.checked)}
              />{" "}
              Associer la position GPS actuelle
            </label>
          </p>
          <button className="primary" type="submit" disabled={busy}>
            {busy ? "Analyse..." : "Analyser l'image"}
          </button>
        </form>
        {error && <p className="error">{error}</p>}
      </div>

      {result && (
        <div className="card">
          <h2>Résultat</h2>
          <p>
            Zone détectée :{" "}
            <span className={`badge ${result.zone.category}`}>
              {result.zone.label}
            </span>
            {result.zone.needs_field_check && (
              <span> — vérification humaine requise sur le terrain</span>
            )}
          </p>
          <p>Modèle : {result.model_backend}</p>
          {result.annotated_image_base64 && (
            <img
              src={`data:image/jpeg;base64,${result.annotated_image_base64}`}
              alt="Détections"
              style={{ maxWidth: "100%", borderRadius: 8 }}
            />
          )}
          <ul className="detected-list">
            {result.detections.map((det, index) => (
              <li key={index}>
                <span>{det.class_name}</span>
                <span>{(det.confidence * 100).toFixed(0)} %</span>
              </li>
            ))}
            {result.detections.length === 0 && <li>Aucun déchet détecté.</li>}
          </ul>
          {result.observation_id && (
            <p>
              Enregistré comme observation d'id {result.observation_id}
              {result.zone.needs_field_check ? " (à faire vérifier)" : ""}.
            </p>
          )}
        </div>
      )}
    </>
  );
}
