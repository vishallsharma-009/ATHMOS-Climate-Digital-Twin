import React from "react";

export default function TimeSlider({ timeline, currentIndex, onIndexChange }) {
  if (!timeline || timeline.length === 0) return null;

  return (
    <div className="bg-gray-800 border border-gray-700 p-4 rounded-lg flex flex-col gap-2">
      <div className="flex justify-between items-center text-sm font-medium text-gray-300">
        <span>Current State (Day 0)</span>
        <span>Forecast Horizon (Day {timeline.length})</span>
      </div>
      <input
        type="range"
        min="0"
        max={timeline.length - 1}
        value={currentIndex}
        onChange={(e) => onIndexChange(parseInt(e.target.value, 10))}
        className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
      />
      <div className="text-center text-xs text-blue-400 font-semibold mt-1">
        Selected: Day {timeline[currentIndex]?.day || currentIndex + 1}
      </div>
    </div>
  );
}
