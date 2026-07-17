import { useEffect, useState } from "react";
import { api } from "../api.js";
import Card from "../components/Card.jsx";

export default function Forecast() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getForecast().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="text-red-400">{error}</p>;
  if (!data) return <p className="text-gray-400">Loading forecast...</p>;

  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">
        {data.horizon_days}-Day Forecast — {data.region}
      </h2>
      <div className="grid grid-cols-3 md:grid-cols-7 gap-3">
        {data.forecast.map((d) => (
          <Card key={d.day} title={`Day ${d.day}`}>
            <p className="text-sm text-blue-400">IMD Rain: {d.imd_rainfall_mm !== undefined ? d.imd_rainfall_mm : 0} mm</p>
            <p className="text-sm text-cyan-400">INSAT Rain: {d.insat_rainfall_mm !== undefined ? d.insat_rainfall_mm : 0} mm</p>
            <p className="text-sm text-orange-400">TMax: {d.tmax_c} °C</p>
            <p className="text-sm text-yellow-400">TMin: {d.tmin_c} °C</p>
          </Card>
        ))}
      </div>
      <p className="text-xs text-gray-500 mt-4">{data.note}</p>
    </div>
  );
}
