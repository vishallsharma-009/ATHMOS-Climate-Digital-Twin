import { useState, useEffect } from "react";
import { useClimateData } from "../context/ClimateContext";
import { api } from "../api";
import MapView from "../components/MapView";
import ClimateCharts from "../components/ClimateCharts";
import { Thermometer, CloudRain, Wind, Play, RotateCcw, AlertTriangle } from "lucide-react";

export default function ScenarioEngine() {
  const { forecast, geoJsonData, loading } = useClimateData();
  const [tempAnomaly, setTempAnomaly] = useState(0);
  const [rainAnomaly, setRainAnomaly] = useState(0);
  const [isSimulating, setIsSimulating] = useState(false);
  
  const [scenarioData, setScenarioData] = useState(null);

  // Derived live feedback before simulation runs
  const heatRisk = Math.min(100, Math.max(0, 50 + (tempAnomaly * 15)));
  const floodRisk = Math.min(100, Math.max(0, 20 + (rainAnomaly * 2)));

  const handleRunSimulation = async () => {
    setIsSimulating(true);
    try {
      const res = await api.getScenario(tempAnomaly, rainAnomaly);
      setScenarioData(res.forecast);
    } catch (e) {
      console.error(e);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleReset = () => {
    setTempAnomaly(0);
    setRainAnomaly(0);
    setScenarioData(null);
  };

  return (
    <div className="flex flex-col h-full p-2 gap-6">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-xl font-bold text-gray-100">Scenario Engine</h2>
          <p className="text-sm text-gray-400">Digital Twin Climate Simulation Lab</p>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-6 min-h-0 flex-1">
        
        {/* Left Panel: Sliders & Live Risks */}
        <div className="w-full lg:w-80 flex flex-col gap-4 overflow-y-auto custom-scrollbar flex-shrink-0">
          
          <div className="glass-panel p-4 flex flex-col gap-4">
            <h3 className="font-semibold text-gray-200 border-b border-gray-800 pb-2">Simulation Parameters</h3>
            
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-400 flex items-center gap-1"><Thermometer size={14}/> Temp Change</span>
                <span className={`font-bold ${tempAnomaly > 0 ? "text-orange-400" : tempAnomaly < 0 ? "text-blue-400" : "text-gray-300"}`}>
                  {tempAnomaly > 0 ? "+" : ""}{tempAnomaly}°C
                </span>
              </div>
              <input type="range" min="-3" max="5" step="0.1" value={tempAnomaly} onChange={(e) => setTempAnomaly(parseFloat(e.target.value))} className="w-full accent-orange-500"/>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-400 flex items-center gap-1"><CloudRain size={14}/> Rainfall Change</span>
                <span className={`font-bold ${rainAnomaly > 0 ? "text-blue-400" : rainAnomaly < 0 ? "text-orange-400" : "text-gray-300"}`}>
                  {rainAnomaly > 0 ? "+" : ""}{rainAnomaly}mm
                </span>
              </div>
              <input type="range" min="-50" max="100" step="5" value={rainAnomaly} onChange={(e) => setRainAnomaly(parseFloat(e.target.value))} className="w-full accent-blue-500"/>
            </div>

            <div className="flex gap-2 mt-4">
              <button onClick={handleRunSimulation} disabled={isSimulating} className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-lg flex items-center justify-center gap-2 transition-all">
                {isSimulating ? <RotateCcw size={16} className="animate-spin" /> : <Play size={16} />} 
                {isSimulating ? "Running..." : "Run Simulation"}
              </button>
              <button onClick={handleReset} className="px-4 bg-gray-800 hover:bg-gray-700 text-gray-300 font-medium rounded-lg transition-all">
                Reset
              </button>
            </div>
          </div>

          <div className="glass-panel p-4 flex-1">
            <h3 className="font-semibold text-gray-200 border-b border-gray-800 pb-2 mb-4">Live Projected Risk</h3>
            <div className="flex flex-col gap-4">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-400">Heat Stress Index</span>
                  <span className={heatRisk > 75 ? "text-red-400" : heatRisk > 50 ? "text-orange-400" : "text-green-400"}>{heatRisk.toFixed(0)}</span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-1.5">
                  <div className={`h-1.5 rounded-full ${heatRisk > 75 ? "bg-red-500" : heatRisk > 50 ? "bg-orange-500" : "bg-green-500"}`} style={{ width: `${heatRisk}%` }}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-400">Flood Risk Index</span>
                  <span className={floodRisk > 75 ? "text-red-400" : floodRisk > 50 ? "text-orange-400" : "text-green-400"}>{floodRisk.toFixed(0)}</span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-1.5">
                  <div className={`h-1.5 rounded-full ${floodRisk > 75 ? "bg-red-500" : floodRisk > 50 ? "bg-orange-500" : "bg-green-500"}`} style={{ width: `${floodRisk}%` }}></div>
                </div>
              </div>

              {heatRisk > 80 && (
                <div className="mt-2 p-2 bg-red-500/10 border border-red-500/30 rounded flex gap-2">
                  <AlertTriangle size={16} className="text-red-400 flex-shrink-0" />
                  <span className="text-xs text-red-200">Critical Heatwave conditions projected. Agricultural yield may drop by 24%.</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Panel: Map & Charts */}
        <div className="flex-1 flex flex-col gap-4 min-h-0">
          <div className="flex-1 glass-panel relative overflow-hidden">
            <div className="absolute top-2 left-2 z-10 bg-gray-900/80 px-2 py-1 rounded text-xs font-medium text-gray-300 border border-gray-700 backdrop-blur">
              {scenarioData ? "Simulated Timeline Map" : "Baseline Forecast Map"}
            </div>
            <MapView geoData={geoJsonData} overlayType={tempAnomaly > 0 ? "temperature" : "rainfall"} />
          </div>

          <div className="h-64 glass-panel p-2">
            <ClimateCharts timeline={scenarioData || forecast} />
          </div>
        </div>

      </div>
    </div>
  );
}
