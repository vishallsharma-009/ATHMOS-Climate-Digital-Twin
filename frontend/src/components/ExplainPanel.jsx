import React from "react";

export default function ExplainPanel({ explainData }) {
  if (!explainData) return null;

  const { global_importance } = explainData;
  const total = Object.values(global_importance).reduce((a, b) => a + b, 0);

  return (
    <div className="bg-gray-800 p-4 rounded-xl border border-gray-700">
      <h3 className="text-gray-300 font-medium mb-3">AI Explainability (SHAP)</h3>
      <p className="text-xs text-gray-400 mb-3">Global Feature Importance driving this timeline:</p>
      <div className="flex flex-col gap-2">
        {Object.entries(global_importance).map(([feature, val]) => {
          const pct = Math.round((val / total) * 100);
          return (
            <div key={feature}>
              <div className="flex justify-between text-xs text-gray-300 mb-1">
                <span className="capitalize">{feature.replace("_", " ")}</span>
                <span>{pct}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-1.5">
                <div className="bg-teal-500 h-1.5 rounded-full" style={{ width: `${pct}%` }}></div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
