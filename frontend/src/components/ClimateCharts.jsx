import React from "react";
import Plot from "react-plotly.js";

export default function ClimateCharts({ timeline }) {
  if (!timeline || timeline.length === 0) return null;

  const days = timeline.map(t => `Day ${t.day}`);
  const tempsMax = timeline.map(t => t.tmax_c !== undefined ? t.tmax_c : t.temperature_c);
  const tempsMin = timeline.map(t => t.tmin_c !== undefined ? t.tmin_c : 0);
  const imdRain = timeline.map(t => t.imd_rainfall_mm !== undefined ? t.imd_rainfall_mm : 0);
  const insatRain = timeline.map(t => t.insat_rainfall_mm !== undefined ? t.insat_rainfall_mm : 0);

  return (
    <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 h-full flex flex-col">
      <h3 className="text-gray-300 font-medium mb-4">7-Day Forecast Trends</h3>
      <div className="flex-1 w-full min-h-[300px]">
        <Plot
          data={[
            {
              x: days,
              y: tempsMax,
              type: "scatter",
              mode: "lines+markers",
              name: "Max Temp (°C)",
              marker: { color: "#f97316" }, // orange-500
              line: { shape: 'spline', smoothing: 1.3 }
            },
            {
              x: days,
              y: tempsMin,
              type: "scatter",
              mode: "lines+markers",
              name: "Min Temp (°C)",
              marker: { color: "#eab308" }, // yellow-500
              line: { shape: 'spline', smoothing: 1.3, dash: 'dot' }
            },
            {
              x: days,
              y: imdRain,
              type: "bar",
              name: "IMD Rain (mm)",
              marker: { color: "#3b82f6" }, // blue-500
              yaxis: "y2"
            },
            {
              x: days,
              y: insatRain,
              type: "bar",
              name: "INSAT Rain (mm)",
              marker: { color: "#06b6d4" }, // cyan-500
              yaxis: "y2"
            }
          ]}
          layout={{
            autosize: true,
            margin: { t: 10, l: 40, r: 40, b: 40 },
            paper_bgcolor: "transparent",
            plot_bgcolor: "transparent",
            font: { color: "#9ca3af" }, // gray-400
            xaxis: {
              showgrid: false,
              zeroline: false
            },
            yaxis: {
              title: "Temperature (°C)",
              showgrid: true,
              gridcolor: "#374151", // gray-700
              zeroline: false
            },
            yaxis2: {
              title: "Rainfall (mm)",
              overlaying: "y",
              side: "right",
              showgrid: false,
              zeroline: false
            },
            legend: {
              orientation: "h",
              y: -0.2
            }
          }}
          useResizeHandler={true}
          style={{ width: "100%", height: "100%" }}
          config={{ displayModeBar: false }}
        />
      </div>
    </div>
  );
}
