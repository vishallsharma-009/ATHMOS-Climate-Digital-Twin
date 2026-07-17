import { useClimateData } from "../context/ClimateContext";
import { Activity, Clock } from "lucide-react";

export default function Header() {
  const { lastUpdated, loading } = useClimateData();

  return (
    <header className="h-16 flex-shrink-0 bg-gray-900 border-b border-gray-800 flex items-center justify-between px-6 z-10 shadow-md">
      <div className="flex items-center gap-3">
        <h1 className="text-xl font-bold text-gray-100 tracking-wide">
          ATHMOS <span className="text-blue-500 font-medium text-sm ml-2 px-2 py-1 bg-blue-500/10 rounded-full border border-blue-500/20">AI Climate Digital Twin</span>
        </h1>
      </div>
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <span className="font-semibold text-gray-300">Scale:</span> 
          <span className="px-2 py-0.5 bg-gray-800 rounded border border-gray-700">Pilot Region</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <Clock size={16} />
          {loading ? (
            <span className="animate-pulse">Syncing...</span>
          ) : (
            <span>Updated: {lastUpdated ? lastUpdated.toLocaleTimeString() : "Never"}</span>
          )}
        </div>
        <div className="flex items-center gap-2 text-sm font-medium">
          <Activity size={16} className="text-green-500" />
          <span className="text-green-500">Live</span>
        </div>
      </div>
    </header>
  );
}
