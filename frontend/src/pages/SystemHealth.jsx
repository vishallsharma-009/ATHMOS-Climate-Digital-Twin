import { useClimateData } from "../context/ClimateContext";
import { Server, Activity, Database, Cpu, HardDrive } from "lucide-react";

export default function SystemHealth() {
  const { dashboard, loading, lastUpdated } = useClimateData();

  const status = dashboard?.system_health?.model_status || "offline";
  const isOnline = status === "initialized" || status === "online" || status === "ready";

  return (
    <div className="flex flex-col gap-6 h-full p-2">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-100 flex items-center gap-2">
            System Health Monitor
          </h2>
          <p className="text-sm text-gray-400">Digital Twin Infrastructure & Pipeline Status</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1 bg-gray-900 border border-gray-700 rounded-lg">
          <span className={`h-2.5 w-2.5 rounded-full ${isOnline ? "bg-green-500 animate-pulse" : "bg-red-500"}`}></span>
          <span className="text-sm font-medium text-gray-300">
            {isOnline ? "All Systems Operational" : "System Degraded"}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-4 flex flex-col gap-1">
          <div className="text-gray-400 text-sm flex items-center gap-2"><Activity size={16}/> Inference Latency</div>
          <div className="text-2xl font-bold text-gray-100">{isOnline ? "24" : "--"}<span className="text-sm text-gray-500 ml-1">ms</span></div>
        </div>
        <div className="glass-panel p-4 flex flex-col gap-1">
          <div className="text-gray-400 text-sm flex items-center gap-2"><Cpu size={16}/> GPU Utilization</div>
          <div className="text-2xl font-bold text-gray-100">{isOnline ? "68" : "--"}<span className="text-sm text-gray-500 ml-1">%</span></div>
        </div>
        <div className="glass-panel p-4 flex flex-col gap-1">
          <div className="text-gray-400 text-sm flex items-center gap-2"><HardDrive size={16}/> Memory Usage</div>
          <div className="text-2xl font-bold text-gray-100">{isOnline ? "14.2" : "--"}<span className="text-sm text-gray-500 ml-1">GB</span></div>
        </div>
        <div className="glass-panel p-4 flex flex-col gap-1">
          <div className="text-gray-400 text-sm flex items-center gap-2"><Database size={16}/> Twin Sync Rate</div>
          <div className="text-2xl font-bold text-gray-100">{isOnline ? "30" : "--"}<span className="text-sm text-gray-500 ml-1">sec</span></div>
        </div>
      </div>

      <div className="flex-1 glass-panel p-6 overflow-y-auto custom-scrollbar">
        <h3 className="font-semibold text-gray-200 border-b border-gray-800 pb-2 mb-6">Data Assimilation Pipeline</h3>
        
        <div className="relative">
          {/* Vertical connecting line */}
          <div className="absolute left-6 top-6 bottom-6 w-0.5 bg-gray-800"></div>

          <div className="flex flex-col gap-8">
            <div className="flex gap-4 relative">
              <div className="w-12 h-12 rounded-full bg-gray-900 border-2 border-blue-500 flex items-center justify-center z-10 shrink-0 shadow-[0_0_15px_rgba(59,130,246,0.3)]">
                <Database size={20} className="text-blue-400" />
              </div>
              <div className="flex-1 bg-gray-800/50 p-4 rounded-lg border border-gray-700">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-semibold text-gray-200">1. IMD & INSAT Data Ingestion</h4>
                    <p className="text-sm text-gray-400 mt-1">Fetching latest satellite imagery and ground station arrays.</p>
                  </div>
                  <span className="px-2 py-1 bg-green-500/10 text-green-400 border border-green-500/20 text-xs rounded">Success</span>
                </div>
              </div>
            </div>

            <div className="flex gap-4 relative">
              <div className="w-12 h-12 rounded-full bg-gray-900 border-2 border-cyan-500 flex items-center justify-center z-10 shrink-0 shadow-[0_0_15px_rgba(6,182,212,0.3)]">
                <Server size={20} className="text-cyan-400" />
              </div>
              <div className="flex-1 bg-gray-800/50 p-4 rounded-lg border border-gray-700">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-semibold text-gray-200">2. Multi-source Data Fusion</h4>
                    <p className="text-sm text-gray-400 mt-1">Aligning spatial resolutions and normalizing tensors.</p>
                  </div>
                  <span className="px-2 py-1 bg-green-500/10 text-green-400 border border-green-500/20 text-xs rounded">Success</span>
                </div>
              </div>
            </div>

            <div className="flex gap-4 relative">
              <div className="w-12 h-12 rounded-full bg-gray-900 border-2 border-purple-500 flex items-center justify-center z-10 shrink-0 shadow-[0_0_15px_rgba(168,85,247,0.3)]">
                <Cpu size={20} className="text-purple-400" />
              </div>
              <div className="flex-1 bg-gray-800/50 p-4 rounded-lg border border-gray-700">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-semibold text-gray-200">3. ConvLSTM AI Inference</h4>
                    <p className="text-sm text-gray-400 mt-1">Generating spatial-temporal forecasts for next 7 days.</p>
                  </div>
                  <span className="px-2 py-1 bg-green-500/10 text-green-400 border border-green-500/20 text-xs rounded">Success</span>
                </div>
              </div>
            </div>

            <div className="flex gap-4 relative">
              <div className="w-12 h-12 rounded-full bg-gray-900 border-2 border-green-500 flex items-center justify-center z-10 shrink-0 shadow-[0_0_15px_rgba(34,197,94,0.3)]">
                <Activity size={20} className="text-green-400" />
              </div>
              <div className="flex-1 bg-gray-800/50 p-4 rounded-lg border border-gray-700">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-semibold text-gray-200">4. Digital Twin Synchronization</h4>
                    <p className="text-sm text-gray-400 mt-1">Updating client dashboards and map layers.</p>
                  </div>
                  <span className="text-xs text-gray-500">Last updated: {lastUpdated?.toLocaleTimeString() || "..."}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
