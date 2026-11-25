const BASE = import.meta.env.VITE_API_URL ?? "";

export async function analyzeImage(file, { sessionId, latitude, longitude, commune, annotate }) {
  const form = new FormData();
  form.append("image", file);
  form.append("session_id", sessionId);
  form.append("annotate", String(annotate));
  if (latitude != null) form.append("latitude", latitude);
  if (longitude != null) form.append("longitude", longitude);
  if (commune) form.append("commune", commune);
  const response = await fetch(`${BASE}/api/analyze`, { method: "POST", body: form });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || `Erreur ${response.status}`);
  }
  return response.json();
}

export async function listObservations(params = {}) {
  const query = new URLSearchParams(params);
  const response = await fetch(`${BASE}/api/observations?${query}`);
  if (!response.ok) throw new Error(`Erreur ${response.status}`);
  return response.json();
}

export async function validateObservation(id, verdict, agent) {
  const response = await fetch(`${BASE}/api/observations/${id}/validate`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ verdict, agent }),
  });
  if (!response.ok) throw new Error(`Erreur ${response.status}`);
  return response.json();
}

export async function refreshHotspots() {
  const response = await fetch(`${BASE}/api/hotspots/refresh`, { method: "POST" });
  if (!response.ok) throw new Error(`Erreur ${response.status}`);
  return response.json();
}

export async function listHotspots() {
  const response = await fetch(`${BASE}/api/hotspots`);
  if (!response.ok) throw new Error(`Erreur ${response.status}`);
  return response.json();
}

export async function fetchStats() {
  const response = await fetch(`${BASE}/api/stats`);
  if (!response.ok) throw new Error(`Erreur ${response.status}`);
  return response.json();
}
