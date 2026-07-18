import { useState } from "react";
import { useClimateData } from "../context/ClimateContext";
import MapView from "../components/MapView";
import { Play, Pause, RotateCcw, FastForward, Activity, Database, Server } from "lucide-react";

export default function LiveDigitalTwin() {
  const { geoJsonData, loading, dashboard } = useClimateData();
  const [overlay, setOverlay] = useState("rainfall");
  const [isPlaying, setIsPlaying] = useState(false);

  return (
    <div className="flex flex-col md:flex-row gap-6 h-full p-2">
      
      {/* Left Area: Map and Controls */}
      <div className="flex-1 flex flex-col gap-4 min-h-0">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <h2 className="text-xl font-bold text-gray-100">Live Digital Twin State</h2>
          <div className="flex flex-wrap gap-2">
            {["rainfall", "temperature", "LST", "SST"].map((mode) => (
              <button
                key={mode}
                onClick={() => setOverlay(mode)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md border transition-all ${
                  overlay === mode 
                  ? "bg-blue-600/20 text-blue-400 border-blue-500/50" 
                  : "bg-gray-900 border-gray-700 text-gray-400 hover:text-gray-200 hover:border-gray-500"
                }`}
              >
                {mode.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Map Container */}
        <div className="flex-1 glass-panel relative overflow-hidden flex flex-col">
          <div className="absolute top-4 left-4 z-10 bg-gray-900/80 backdrop-blur border border-gray-700 p-3 rounded-lg shadow-xl">
            <h4 className="text-xs font-semibold text-gray-300 uppercase mb-1">Gujarat Pilot Region</h4>
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></span>
              <span className="text-sm font-medium text-green-400">Synchronized</span>
            </div>
          </div>
          
          <div className="flex-1 z-0 relative">
            <MapView geoData={geoJsonData} overlayType={overlay} />
            {loading && (
              <div className="absolute inset-0 bg-gray-900/40 backdrop-blur-sm z-50 flex items-center justify-center">
                <span className="animate-pulse font-medium text-blue-400">Loading Map Data...</span>
              </div>
            )}
          </div>

          {/* Time Controls */}
          <div className="h-16 bg-gray-900/90 border-t border-gray-800 flex items-center px-4 gap-4 z-10">
            <div className="flex gap-2">
              <button onClick={() => setIsPlaying(!isPlaying)} className="p-2 hover:bg-gray-800 rounded-full text-gray-300 transition-colors">
                {isPlaying ? <Pause size={18} /> : <Play size={18} />}
              </button>
              <button className="p-2 hover:bg-gray-800 rounded-full text-gray-300 transition-colors">
                <RotateCcw size={18} />
              </button>
              <button className="p-2 hover:bg-gray-800 rounded-full text-gray-300 transition-colors">
                <FastForward size={18} />
              </button>
            </div>
            <div className="flex-1 px-4">
              <input type="range" className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500" min="2020" max="2026" defaultValue="2026" />
            </div>
            <div className="text-sm font-mono text-gray-400 bg-gray-800 px-3 py-1 rounded border border-gray-700">
              2026-07-18
            </div>
          </div>
        </div>
      </div>

      {/* Right Side Panel */}
      <div className="w-full md:w-80 flex flex-col gap-4 flex-shrink-0">
        
        {/* Assimilation Status */}
        <div className="glass-panel p-4 flex flex-col gap-4">
          <h3 className="font-semibold text-gray-200 border-b border-gray-800 pb-2 flex items-center gap-2">
            <Database size={16} className="text-blue-400" /> Data Assimilation
          </h3>
          
          <div className="flex flex-col gap-4">
            {/* IMD */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-gray-400">IMD Ground Stations</span>
                <span className="text-green-400 font-medium">Online</span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-1">
                <div className="bg-green-500 h-1 rounded-full w-full"></div>
              </div>
            </div>
            
            {/* INSAT */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-gray-400">INSAT-3D Satellite</span>
                <span className="text-green-400 font-medium">Synced</span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-1">
                <div className="bg-green-500 h-1 rounded-full w-[95%]"></div>
              </div>
            </div>

            {/* Fusion */}
            <div className="mt-2 p-3 bg-gray-800/50 rounded-lg border border-gray-700">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-semibold text-gray-300">ConvLSTM Fusion</span>
                <Activity size={14} className="text-blue-400" />
              </div>
              <p className="text-xs text-gray-400">AI prediction model is receiving live fused sequences. Latency: <span className="text-blue-400">24ms</span></p>
            </div>
          </div>
        </div>

        {/* Global Summary */}
        <div className="glass-panel p-4 flex-1">
          <h3 className="font-semibold text-gray-200 border-b border-gray-800 pb-2 flex items-center gap-2">
            <Server size={16} className="text-purple-400" /> Twin Health
          </h3>
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700 text-center">
              <div className="text-xl font-bold text-gray-200">{dashboard?.system_status === "operational" ? "99.8%" : "N/A"}</div>
              <div className="text-xs text-gray-500 mt-1">Accuracy</div>
            </div>
            <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700 text-center">
              <div className="text-xl font-bold text-green-400">{dashboard?.system_status === "operational" ? "OK" : "Wait"}</div>
              <div className="text-xs text-gray-500 mt-1">Pipeline</div>
            </div>
          </div>
        </div>
        
      </div>
    </div>
  );
}
