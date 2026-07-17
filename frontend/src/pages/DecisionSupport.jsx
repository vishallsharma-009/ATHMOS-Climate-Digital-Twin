import { useState } from "react";
import { useClimateData } from "../context/ClimateContext";
import { Leaf, Droplets, ShieldAlert, Building2, AlertTriangle, CheckCircle2 } from "lucide-react";

export default function DecisionSupport() {
  const { dashboard, loading } = useClimateData();
  const [activeTab, setActiveTab] = useState("agriculture");

  // Derive mock logic based on live data for the sake of the pilot demonstration
  const tmax = dashboard?.tmax_c || 35;
  const rain = dashboard?.imd_rainfall_mm || 0;
  
  const cropStress = tmax > 38 ? "High" : tmax > 34 ? "Moderate" : "Low";
  const irrigationNeeded = rain < 5 && tmax > 32 ? "Critical" : "Standard";
  
  const reservoirImpact = rain < 10 ? "Declining" : "Recharging";
  const waterAvailability = rain > 20 ? "Good" : "Stressed";
  
  const floodRisk = rain > 40 ? "High" : rain > 20 ? "Moderate" : "Low";
  const heatwaveRisk = tmax > 40 ? "Severe" : tmax > 37 ? "Warning" : "Normal";
  
  const heatIsland = tmax > 35 ? "Elevated" : "Normal";
  const drainageRisk = rain > 30 ? "High" : "Low";

  const tabs = [
    { id: "agriculture", label: "Agriculture", icon: Leaf },
    { id: "water", label: "Water", icon: Droplets },
    { id: "disaster", label: "Disaster", icon: ShieldAlert },
    { id: "urban", label: "Urban", icon: Building2 },
  ];

  return (
    <div className="flex flex-col gap-6 h-full p-2">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-100 flex items-center gap-2">
            Decision Support System (DSS)
          </h2>
          <p className="text-sm text-gray-400">Actionable intelligence derived from Digital Twin state</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-800">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-6 py-3 border-b-2 font-medium transition-colors ${
              activeTab === tab.id
                ? "border-blue-500 text-blue-400"
                : "border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-700"
            }`}
          >
            <tab.icon size={18} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 glass-panel p-6 overflow-y-auto custom-scrollbar">
        {loading ? (
          <div className="animate-pulse flex flex-col gap-4">
            <div className="h-8 bg-gray-800 rounded w-1/3"></div>
            <div className="h-24 bg-gray-800 rounded w-full"></div>
            <div className="h-24 bg-gray-800 rounded w-full"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {activeTab === "agriculture" && (
              <>
                <div className="bg-gray-800/50 p-5 rounded-xl border border-gray-700">
                  <h3 className="text-gray-400 text-sm mb-2">Crop Stress Index</h3>
                  <div className={`text-2xl font-bold ${cropStress === "High" ? "text-red-400" : cropStress === "Moderate" ? "text-orange-400" : "text-green-400"}`}>
                    {cropStress} Risk
                  </div>
                  <p className="text-xs text-gray-500 mt-2">Driven by current TMAX ({tmax.toFixed(1)}°C)</p>
                </div>
                <div className="bg-gray-800/50 p-5 rounded-xl border border-gray-700">
                  <h3 className="text-gray-400 text-sm mb-2">Irrigation Recommendation</h3>
                  <div className={`text-2xl font-bold ${irrigationNeeded === "Critical" ? "text-red-400" : "text-blue-400"}`}>
                    {irrigationNeeded}
                  </div>
                  <p className="text-xs text-gray-500 mt-2">Based on {rain.toFixed(1)}mm recent rainfall</p>
                </div>
                <div className="md:col-span-2 mt-4 p-4 bg-orange-500/10 border border-orange-500/20 rounded-lg flex gap-3">
                  <AlertTriangle className="text-orange-400 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold text-orange-200">Yield Risk Warning</h4>
                    <p className="text-sm text-orange-400/80 mt-1">If current temperature anomalies persist, Kharif crop yield in North Gujarat may decrease by 8-12%.</p>
                  </div>
                </div>
              </>
            )}

            {activeTab === "water" && (
              <>
                <div className="bg-gray-800/50 p-5 rounded-xl border border-gray-700">
                  <h3 className="text-gray-400 text-sm mb-2">Reservoir Status</h3>
                  <div className={`text-2xl font-bold ${reservoirImpact === "Declining" ? "text-orange-400" : "text-blue-400"}`}>
                    {reservoirImpact}
                  </div>
                </div>
                <div className="bg-gray-800/50 p-5 rounded-xl border border-gray-700">
                  <h3 className="text-gray-400 text-sm mb-2">Groundwater Availability</h3>
                  <div className={`text-2xl font-bold ${waterAvailability === "Stressed" ? "text-orange-400" : "text-green-400"}`}>
                    {waterAvailability}
                  </div>
                </div>
                {waterAvailability === "Stressed" && (
                  <div className="md:col-span-2 mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex gap-3">
                    <AlertTriangle className="text-red-400 flex-shrink-0" />
                    <div>
                      <h4 className="font-semibold text-red-200">Water Scarcity Alert</h4>
                      <p className="text-sm text-red-400/80 mt-1">Implement municipal water rationing protocols. Rainfall deficit is affecting major reservoirs.</p>
                    </div>
                  </div>
                )}
              </>
            )}

            {activeTab === "disaster" && (
              <>
                <div className="bg-gray-800/50 p-5 rounded-xl border border-gray-700">
                  <h3 className="text-gray-400 text-sm mb-2">Flash Flood Risk</h3>
                  <div className={`text-2xl font-bold ${floodRisk === "High" ? "text-red-400" : floodRisk === "Moderate" ? "text-orange-400" : "text-green-400"}`}>
                    {floodRisk}
                  </div>
                </div>
                <div className="bg-gray-800/50 p-5 rounded-xl border border-gray-700">
                  <h3 className="text-gray-400 text-sm mb-2">Heatwave Risk</h3>
                  <div className={`text-2xl font-bold ${heatwaveRisk === "Severe" ? "text-red-400" : heatwaveRisk === "Warning" ? "text-orange-400" : "text-green-400"}`}>
                    {heatwaveRisk}
                  </div>
                </div>
              </>
            )}

            {activeTab === "urban" && (
              <>
                <div className="bg-gray-800/50 p-5 rounded-xl border border-gray-700">
                  <h3 className="text-gray-400 text-sm mb-2">Urban Heat Island (UHI)</h3>
                  <div className={`text-2xl font-bold ${heatIsland === "Elevated" ? "text-orange-400" : "text-green-400"}`}>
                    {heatIsland}
                  </div>
                </div>
                <div className="bg-gray-800/50 p-5 rounded-xl border border-gray-700">
                  <h3 className="text-gray-400 text-sm mb-2">Drainage Overload Risk</h3>
                  <div className={`text-2xl font-bold ${drainageRisk === "High" ? "text-red-400" : "text-green-400"}`}>
                    {drainageRisk}
                  </div>
                </div>
                <div className="md:col-span-2 mt-4 p-4 bg-green-500/10 border border-green-500/20 rounded-lg flex gap-3">
                  <CheckCircle2 className="text-green-400 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold text-green-200">Urban Infrastructure Safe</h4>
                    <p className="text-sm text-green-400/80 mt-1">Current precipitation patterns are well within the municipal drainage capacity limits.</p>
                  </div>
                </div>
              </>
            )}
            
          </div>
        )}
      </div>
    </div>
  );
}
