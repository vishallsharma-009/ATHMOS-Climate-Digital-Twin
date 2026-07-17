import React, { useState } from "react";
import { api } from "../api";

export default function ScenarioControl({ onScenarioRun }) {
  const [tempAnomaly, setTempAnomaly] = useState(0);
  const [rainAnomaly, setRainAnomaly] = useState(0);
  const [loading, setLoading] = useState(false);

  const handleRun = async () => {
    setLoading(true);
    try {
      const res = await api.getScenario(tempAnomaly, rainAnomaly);
      onScenarioRun(res.forecast);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setTempAnomaly(0);
    setRainAnomaly(0);
    setLoading(true);
    try {
      const res = await api.getForecast();
      onScenarioRun(res.forecast);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-800 p-4 rounded-xl border border-gray-700">
      <h3 className="text-gray-300 font-medium mb-4">What-If Scenarios</h3>
      <div className="flex flex-col gap-3">
        <div>
          <label className="text-xs text-gray-400 block mb-1">
            Max Temp Anomaly ({tempAnomaly > 0 ? "+" : ""}{tempAnomaly}°C)
          </label>
          <input
            type="range"
            min="-5"
            max="5"
            step="0.5"
            value={tempAnomaly}
            onChange={(e) => setTempAnomaly(parseFloat(e.target.value))}
            className="w-full accent-orange-500"
          />
        </div>
        <div>
          <label className="text-xs text-gray-400 block mb-1">
            Rainfall Anomaly ({rainAnomaly > 0 ? "+" : ""}{rainAnomaly}mm)
          </label>
          <input
            type="range"
            min="-50"
            max="50"
            step="5"
            value={rainAnomaly}
            onChange={(e) => setRainAnomaly(parseFloat(e.target.value))}
            className="w-full accent-blue-500"
          />
        </div>
        <div className="flex gap-2 mt-2">
          <button 
            onClick={handleRun} 
            disabled={loading}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm py-1.5 rounded disabled:opacity-50 transition-colors"
          >
            {loading ? "Simulating..." : "Simulate"}
          </button>
          <button 
            onClick={handleReset} 
            disabled={loading}
            className="flex-1 bg-gray-700 hover:bg-gray-600 text-white text-sm py-1.5 rounded disabled:opacity-50 transition-colors"
          >
            Reset
          </button>
        </div>
      </div>
    </div>
  );
}
