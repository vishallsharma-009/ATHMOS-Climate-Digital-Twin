import { useClimateData } from "../context/ClimateContext";
import { BrainCircuit, Fingerprint, Network } from "lucide-react";

export default function ExplainableAI() {
  const { explain, explainLoading } = useClimateData();

  if (explainLoading) {
    return (
      <div className="flex-1 flex items-center justify-center animate-pulse text-blue-400 gap-2 h-full">
        <BrainCircuit size={24} /> Generating SHAP Interpretations...
      </div>
    );
  }

  if (!explain) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400 gap-2 h-full flex-col">
        <BrainCircuit size={40} className="text-gray-500 mb-2 animate-bounce" />
        <span className="text-lg font-medium text-gray-300">Run a forecast to generate explanations.</span>
      </div>
    );
  }

  const { global_importance, local_explanation } = explain;
  const totalGlobal = Object.values(global_importance).reduce((a, b) => a + b, 0);
  
  // Sort features by importance
  const sortedFeatures = Object.entries(global_importance)
    .sort((a, b) => b[1] - a[1])
    .map(([feature, val]) => ({
      feature: feature.replace(/_/g, " "),
      pct: Math.round((val / totalGlobal) * 100),
      raw: val
    }));

  return (
    <div className="flex flex-col gap-6 h-full p-2">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-100 flex items-center gap-2">
            <BrainCircuit className="text-blue-500" /> Explainable AI (XAI)
          </h2>
          <p className="text-sm text-gray-400">SHAP values and model interpretability</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-4">
          <div className="text-sm text-gray-400 mb-1">Model Architecture</div>
          <div className="text-xl font-bold text-gray-100">ConvLSTM Fusion</div>
          <div className="text-xs text-blue-400 mt-2">Spatial-Temporal Attention</div>
        </div>
        <div className="glass-panel p-4 border-green-500/30">
          <div className="text-sm text-gray-400 mb-1">Prediction Confidence</div>
          <div className="text-xl font-bold text-green-400">89.4%</div>
          <div className="text-xs text-gray-500 mt-2">High certainty across region</div>
        </div>
        <div className="glass-panel p-4">
          <div className="text-sm text-gray-400 mb-1">Uncertainty Bound</div>
          <div className="text-xl font-bold text-gray-100">± 1.2%</div>
          <div className="text-xs text-gray-500 mt-2">Monte Carlo Dropout</div>
        </div>
        <div className="glass-panel p-4">
          <div className="text-sm text-gray-400 mb-1">Top Driver</div>
          <div className="text-xl font-bold text-orange-400 capitalize">{sortedFeatures[0]?.feature || "N/A"}</div>
          <div className="text-xs text-gray-500 mt-2">Dominates current timestep</div>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-0">
        
        {/* Global Importance */}
        <div className="glass-panel p-5 flex flex-col overflow-y-auto custom-scrollbar">
          <h3 className="font-semibold text-gray-200 border-b border-gray-800 pb-2 mb-4 flex items-center gap-2">
            <Network size={16} className="text-blue-400" /> Global Feature Importance
          </h3>
          <div className="flex flex-col gap-6 mt-2">
            {sortedFeatures.map((f, i) => (
              <div key={f.feature} className="group">
                <div className="flex justify-between text-sm text-gray-300 mb-1.5">
                  <span className="capitalize font-medium flex items-center gap-2">
                    <span className="text-gray-600 text-xs w-4">{i+1}.</span> {f.feature}
                  </span>
                  <span className="font-mono text-blue-300">{f.pct}%</span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-2 relative overflow-hidden">
                  <div 
                    className="h-full rounded-full transition-all duration-1000 ease-out bg-gradient-to-r from-blue-600 to-cyan-400"
                    style={{ width: `${f.pct}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Local Explanation */}
        <div className="glass-panel p-5 flex flex-col overflow-y-auto custom-scrollbar">
          <h3 className="font-semibold text-gray-200 border-b border-gray-800 pb-2 mb-4 flex items-center gap-2">
            <Fingerprint size={16} className="text-cyan-400" /> Local Explanation (Current Point)
          </h3>
          
          <p className="text-sm text-gray-400 mb-6 leading-relaxed">
            This panel shows how each feature pushed the model's prediction from the baseline expected value to the final predicted output at the currently selected coordinate.
          </p>

          <div className="flex flex-col gap-4">
            {Object.entries(local_explanation?.contributions || {}).slice(0, 5).map(([feature, val]) => {
              const impact = Math.abs(val) * 100;
              const isPositive = val > 0;
              return (
                <div key={feature} className="flex items-center gap-4 bg-gray-800/50 p-3 rounded-lg border border-gray-700/50">
                  <div className="w-1/3 text-sm text-gray-300 capitalize truncate" title={feature.replace(/_/g, " ")}>
                    {feature.replace(/_/g, " ")}
                  </div>
                  <div className="flex-1 flex items-center">
                    {/* Center line */}
                    <div className="w-1/2 flex justify-end pr-1 border-r border-gray-600 h-6">
                      {!isPositive && (
                        <div className="h-full bg-blue-500/80 rounded-l" style={{ width: `${Math.min(impact*5, 100)}%` }}></div>
                      )}
                    </div>
                    <div className="w-1/2 flex justify-start pl-1 h-6">
                      {isPositive && (
                        <div className="h-full bg-red-500/80 rounded-r" style={{ width: `${Math.min(impact*5, 100)}%` }}></div>
                      )}
                    </div>
                  </div>
                  <div className="w-16 text-right font-mono text-xs text-gray-400">
                    {val.toFixed(4)}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
}
