import { useState } from "react";
import { useClimateData } from "../context/ClimateContext";
import ClimateCharts from "../components/ClimateCharts";
import MapView from "../components/MapView";
import { Calendar, Droplets, Thermometer, AlertCircle } from "lucide-react";

export default function ForecastLab() {
  const { forecast, geoJsonData, loading } = useClimateData();
  const [horizon, setHorizon] = useState("7day");
  
  // Safe extraction for the timeline based on horizon
  const visibleTimeline = forecast ? forecast.slice(0, horizon === "3day" ? 3 : horizon === "tomorrow" ? 2 : horizon === "today" ? 1 : 7) : [];
  
  // Aggregate mock metrics
  const expectedRain = visibleTimeline.reduce((acc, curr) => acc + (curr.imd_rainfall_mm || 0), 0).toFixed(1);
  const maxTemp = Math.max(...visibleTimeline.map(t => t.tmax_c || 0)).toFixed(1);

  return (
    <div className="flex flex-col gap-6 h-full p-2">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-100">Forecast Lab</h2>
          <p className="text-sm text-gray-400">Professional predictive analysis timeline</p>
        </div>
        
        <div className="flex gap-2 bg-gray-900 p-1 rounded-lg border border-gray-800">
          {[
            { id: "today", label: "Today" },
            { id: "tomorrow", label: "Tomorrow" },
            { id: "3day", label: "3 Day" },
            { id: "7day", label: "7 Day" }
          ].map(h => (
            <button
              key={h.id}
              onClick={() => setHorizon(h.id)}
              className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
                horizon === h.id 
                ? "bg-blue-600/20 text-blue-400 border border-blue-500/30" 
                : "text-gray-400 hover:text-gray-200 hover:bg-gray-800"
              }`}
            >
              {h.label}
            </button>
          ))}
        </div>
      </div>

      {/* Aggregate Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-panel p-4 flex items-center gap-4">
          <div className="h-12 w-12 rounded-full bg-blue-500/10 flex items-center justify-center border border-blue-500/20">
            <Droplets className="text-blue-400" />
          </div>
          <div>
            <div className="text-sm text-gray-400">Expected Rain</div>
            <div className="text-xl font-bold text-gray-100">{expectedRain} <span className="text-sm text-gray-500">mm</span></div>
          </div>
        </div>
        
        <div className="glass-panel p-4 flex items-center gap-4">
          <div className="h-12 w-12 rounded-full bg-orange-500/10 flex items-center justify-center border border-orange-500/20">
            <Thermometer className="text-orange-400" />
          </div>
          <div>
            <div className="text-sm text-gray-400">Peak Temperature</div>
            <div className="text-xl font-bold text-gray-100">{maxTemp} <span className="text-sm text-gray-500">°C</span></div>
          </div>
        </div>

        <div className="glass-panel p-4 flex items-center gap-4">
          <div className="h-12 w-12 rounded-full bg-green-500/10 flex items-center justify-center border border-green-500/20">
            <Calendar className="text-green-400" />
          </div>
          <div>
            <div className="text-sm text-gray-400">Model Confidence</div>
            <div className="text-xl font-bold text-gray-100">89.4 <span className="text-sm text-gray-500">%</span></div>
          </div>
        </div>

        <div className="glass-panel p-4 flex items-center gap-4 border-orange-500/30">
          <div className="h-12 w-12 rounded-full bg-red-500/10 flex items-center justify-center border border-red-500/20">
            <AlertCircle className="text-red-400" />
          </div>
          <div>
            <div className="text-sm text-gray-400">Expected Extremes</div>
            <div className="text-xl font-bold text-red-400">1 <span className="text-sm text-gray-500">Warning</span></div>
          </div>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-0">
        <div className="lg:col-span-2 glass-panel p-2 flex flex-col">
          {loading ? (
            <div className="flex-1 flex items-center justify-center animate-pulse text-blue-400">Crunching timeline...</div>
          ) : (
            <ClimateCharts timeline={visibleTimeline} />
          )}
        </div>
        
        <div className="glass-panel flex flex-col overflow-hidden relative">
          <div className="absolute top-2 left-2 z-10 bg-gray-900/80 px-2 py-1 rounded text-xs text-gray-300 border border-gray-700 backdrop-blur">
            Forecast Spatial Distribution
          </div>
          <MapView geoData={geoJsonData} overlayType="temperature" />
        </div>
      </div>
    </div>
  );
}
