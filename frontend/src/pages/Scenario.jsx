import { useEffect, useState } from "react";
import { api } from "../api.js";
import Card from "../components/Card.jsx";

export default function Scenario() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getScenario().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="text-red-400">{error}</p>;
  if (!data) return <p className="text-gray-400">Loading scenario...</p>;

  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">
        What-If Scenario Simulator — {data.region}
      </h2>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <Card title="Rainfall Change">{data.rainfall_change_pct}%</Card>
        <Card title="Temperature Change">
          {data.temperature_change_c} °C
        </Card>
        <Card title="Crop Water Stress">
          {data.crop_water_stress_pct ?? "—"}
        </Card>
        <Card title="Flood Risk">{data.flood_risk_pct ?? "—"}</Card>
        <Card title="Yield Anomaly">{data.yield_anomaly_pct ?? "—"}</Card>
      </div>
      <p className="text-xs text-gray-500 mt-4">{data.note}</p>
    </div>
  );
}
