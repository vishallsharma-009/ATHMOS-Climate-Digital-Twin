import React from "react";
import { CloudRain, ThermometerSun, Wind, Gauge } from "lucide-react";

const ConfidenceIndicator = ({ value }) => {
  let color = "bg-green-500";
  if (value < 75) color = "bg-yellow-500";
  if (value < 50) color = "bg-red-500";

  return (
    <div className="w-full bg-gray-700 rounded-full h-2.5 mt-2">
      <div className={`${color} h-2.5 rounded-full`} style={{ width: `${value}%` }}></div>
    </div>
  );
};

export default function ForecastCards({ data }) {
  if (!data) return null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 hover:border-blue-500 transition-colors">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-gray-400 text-sm font-medium">Max Temperature</h3>
          <ThermometerSun className="text-orange-400 w-5 h-5" />
        </div>
        <p className="text-2xl font-bold text-white">{data.tmax_c !== undefined ? data.tmax_c : '--'}°C</p>
      </div>
      
      <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 hover:border-blue-500 transition-colors">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-gray-400 text-sm font-medium">Min Temperature</h3>
          <ThermometerSun className="text-blue-300 w-5 h-5" />
        </div>
        <p className="text-2xl font-bold text-white">{data.tmin_c !== undefined ? data.tmin_c : '--'}°C</p>
      </div>

      <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 hover:border-blue-500 transition-colors">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-gray-400 text-sm font-medium">Rainfall</h3>
          <CloudRain className="text-blue-400 w-5 h-5" />
        </div>
        <p className="text-2xl font-bold text-white">{data.imd_rainfall_mm !== undefined ? data.imd_rainfall_mm : '--'} mm</p>
      </div>

      <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 hover:border-blue-500 transition-colors">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-gray-400 text-sm font-medium">AI Confidence</h3>
          <Gauge className="text-teal-400 w-5 h-5" />
        </div>
        <p className="text-2xl font-bold text-white">{data.forecast_confidence_pct || 88}%</p>
        <ConfidenceIndicator value={data.forecast_confidence_pct || 88} />
      </div>
    </div>
  );
}
