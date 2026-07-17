import { useEffect, useState } from "react";
import { api } from "../api.js";
import MapView from "../components/MapView.jsx";
import ForecastCards from "../components/ForecastCards.jsx";
import TimeSlider from "../components/TimeSlider.jsx";
import ClimateCharts from "../components/ClimateCharts.jsx";
import ScenarioControl from "../components/ScenarioControl.jsx";
import ExplainPanel from "../components/ExplainPanel.jsx";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [explainData, setExplainData] = useState(null);
  const [regions, setRegions] = useState([]);
  const [selectedRegion, setSelectedRegion] = useState("");
  const [geoData, setGeoData] = useState(null);
  const [error, setError] = useState(null);
  const [timeIndex, setTimeIndex] = useState(0);

  useEffect(() => {
    Promise.all([api.getDashboard(), api.getForecast(), api.getExplain(), api.getRegions()])
      .then(([dashboardData, forecastData, explain, regs]) => {
        setData(dashboardData);
        setForecast(forecastData.forecast);
        setExplainData(explain);
        setRegions(regs);
        if (regs.length > 0) {
          setSelectedRegion(regs[0]);
        }
      })
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (selectedRegion) {
      api.getGeojson(selectedRegion)
        .then(data => setGeoData(data))
        .catch(err => console.error("Failed to load geojson for region", err));
    }
  }, [selectedRegion]);

  if (error) return <p className="text-red-400">{error}</p>;
  if (!data || !forecast) return <p className="text-gray-400">Loading digital twin...</p>;

  const currentMetrics = timeIndex === 0 ? data : forecast[timeIndex];

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)] gap-4">
      {/* Top row: Metrics */}
      <div className="flex-shrink-0">
        <ForecastCards data={currentMetrics} />
      </div>

      {/* Main row: Map + Sidebar */}
      <div className="flex-1 flex flex-col md:flex-row gap-4 min-h-0">
        {/* Left column: Leaflet Map */}
        <div className="flex-1 rounded-xl overflow-hidden border border-gray-700 shadow-xl shadow-black/50 h-full flex flex-col">
          <div className="p-3 bg-gray-800 border-b border-gray-700 font-semibold text-gray-200 flex justify-between items-center">
            <span>Spatial Distribution</span>
            {regions.length > 0 && (
              <select 
                value={selectedRegion}
                onChange={(e) => setSelectedRegion(e.target.value)}
                className="bg-gray-900 border border-gray-600 text-sm rounded px-2 py-1 outline-none focus:border-blue-500 transition-colors"
              >
                {regions.map(r => (
                  <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>
                ))}
              </select>
            )}
          </div>
          <div className="flex-1 w-full h-full relative z-0">
            <MapView geoData={geoData} />
          </div>
        </div>

        {/* Right column: Charts & Controls */}
        <div className="w-full md:w-96 flex flex-col gap-4 flex-shrink-0 overflow-y-auto pr-2 custom-scrollbar">
          <ScenarioControl onScenarioRun={setForecast} />
          <div className="bg-gray-800 p-4 rounded-xl border border-gray-700">
            <h3 className="text-gray-300 font-medium mb-4">Timeline Controls</h3>
            <TimeSlider 
              timeline={forecast} 
              currentIndex={timeIndex} 
              onIndexChange={setTimeIndex} 
            />
          </div>
          <ExplainPanel explainData={explainData} />
          <div className="min-h-[300px]">
            <ClimateCharts timeline={forecast} />
          </div>
        </div>
      </div>
    </div>
  );
}
