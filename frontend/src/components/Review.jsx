import React, { useCallback, useEffect, useState } from "react";
import { listObservations, validateObservation } from "../api.js";

export default function Review() {
  const [observations, setObservations] = useState([]);
  const [message, setMessage] = useState(null);
  const [agent, setAgent] = useState("agent-01");

  const load = useCallback(() => {
    listObservations({ limit: 200 })
      .then(setObservations)
      .catch((err) => setMessage(err.message));
  }, []);

  useEffect(load, [load]);

  async function validate(id, verdict) {
    try {
      const updated = await validateObservation(id, verdict, agent);
      setObservations((prev) =>
        prev.map((obs) => (obs.id === id ? { ...obs, ...updated } : obs))
      );
      setMessage(`Observation ${id} : ${verdict === "confirmed" ? "confirmée" : "rejetée"}.`);
    } catch (err) {
      setMessage(err.message);
    }
  }

  const pending = observations.filter((obs) => obs.validation_status === "pending");

  return (
    <div className="card">
      <h2>Validation des observations</h2>
      <p>
        Agent terrain : <input value={agent} onChange={(e) => setAgent(e.target.value)} />
      </p>
      {message && <p>{message}</p>}
      <p>{pending.length} observation(s) en attente de vérification.</p>
      <table className="observations">
        <thead>
          <tr>
            <th>#</th>
            <th>Session</th>
            <th>Commune</th>
            <th>Zone</th>
            <th>Objets</th>
            <th>Statut</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {pending.map((obs) => (
            <tr key={obs.id}>
              <td>{obs.id}</td>
              <td>{obs.session_id}</td>
              <td>{obs.commune || "—"}</td>
              <td>
                <span className={`badge ${obs.zone_category}`}>
                  {obs.zone_category}
                </span>
              </td>
              <td>{obs.detections_count}</td>
              <td>{obs.validation_status}</td>
              <td>
                <button className="primary" onClick={() => validate(obs.id, "confirmed")}>
                  Confirmer
                </button>{" "}
                <button className="secondary" onClick={() => validate(obs.id, "rejected")}>
                  Rejeter
                </button>
              </td>
            </tr>
          ))}
          {pending.length === 0 && (
            <tr>
              <td colSpan={7}>Aucune observation en attente.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
