import { Save } from "lucide-react";

export default function Settings() {
  return (
    <div className="flex flex-col gap-6 h-full p-2 max-w-4xl mx-auto w-full">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-100">System Settings</h2>
          <p className="text-sm text-gray-400">Configure Digital Twin preferences</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors">
          <Save size={16} /> Save Changes
        </button>
      </div>

      <div className="flex flex-col gap-6">
        
        {/* API Settings */}
        <div className="glass-panel p-6">
          <h3 className="font-semibold text-gray-200 border-b border-gray-800 pb-3 mb-4">Backend Connection</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">API Endpoint URL</label>
              <input type="text" defaultValue="http://localhost:8000" className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-blue-500 transition-colors" />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Data Polling Interval (seconds)</label>
              <input type="number" defaultValue="30" className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-blue-500 transition-colors" />
            </div>
          </div>
        </div>

        {/* Display Settings */}
        <div className="glass-panel p-6">
          <h3 className="font-semibold text-gray-200 border-b border-gray-800 pb-3 mb-4">Display Preferences</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Default Region Scale</label>
              <select className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-blue-500 transition-colors">
                <option>Gujarat (Pilot)</option>
                <option>Maharashtra</option>
                <option>National Level</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Temperature Unit</label>
              <select className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-blue-500 transition-colors">
                <option>Celsius (°C)</option>
                <option>Fahrenheit (°F)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Model Settings */}
        <div className="glass-panel p-6">
          <h3 className="font-semibold text-gray-200 border-b border-gray-800 pb-3 mb-4">AI Model Configuration</h3>
          <div className="space-y-3">
            <label className="flex items-center gap-3">
              <input type="checkbox" defaultChecked className="w-4 h-4 rounded border-gray-700 bg-gray-900 text-blue-500 focus:ring-blue-500 focus:ring-offset-gray-900" />
              <span className="text-sm text-gray-300">Enable real-time SHAP explainability</span>
            </label>
            <label className="flex items-center gap-3">
              <input type="checkbox" defaultChecked className="w-4 h-4 rounded border-gray-700 bg-gray-900 text-blue-500 focus:ring-blue-500 focus:ring-offset-gray-900" />
              <span className="text-sm text-gray-300">Auto-trigger Data Assimilation on IMD sync</span>
            </label>
            <label className="flex items-center gap-3">
              <input type="checkbox" className="w-4 h-4 rounded border-gray-700 bg-gray-900 text-blue-500 focus:ring-blue-500 focus:ring-offset-gray-900" />
              <span className="text-sm text-gray-300">Enable experimental anomaly alerts (Strict Thresholds)</span>
            </label>
          </div>
        </div>

      </div>
    </div>
  );
}
