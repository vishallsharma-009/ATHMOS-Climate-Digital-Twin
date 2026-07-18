const BASE_URL = "http://localhost:8000";

async function get(path) {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) throw new Error(`Request failed: ${path}`);
  return res.json();
}

export const api = {
  getDashboard: () => get("/dashboard"),
  getForecast: () => get("/forecast"),
  getScenario: (temp = 0, rain = 0) => get(`/scenario?temp_anomaly=${temp}&rain_anomaly=${rain}`),
  getExplain: () => get("/explain"),
  getRegions: () => get("/regions"),
  getGeojson: (region = "gujarat") => get(`/geojson?region=${region}`),
};
