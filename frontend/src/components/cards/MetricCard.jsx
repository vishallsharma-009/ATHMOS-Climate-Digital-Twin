import { ArrowUp, ArrowDown, Activity } from "lucide-react";

export default function MetricCard({ title, value, unit, trend, icon: Icon, loading }) {
  return (
    <div className="glass-panel p-4 flex flex-col gap-2 relative overflow-hidden group">
      {/* Decorative gradient blob */}
      <div className="absolute -right-6 -top-6 w-24 h-24 bg-blue-500/10 rounded-full blur-2xl group-hover:bg-blue-500/20 transition-all duration-500"></div>
      
      <div className="flex justify-between items-start z-10">
        <span className="text-sm font-medium text-gray-400">{title}</span>
        {Icon ? <Icon size={18} className="text-blue-400" /> : <Activity size={18} className="text-gray-500" />}
      </div>
      
      <div className="flex items-baseline gap-1 z-10 mt-2">
        {loading ? (
          <div className="h-8 w-24 bg-gray-800 rounded animate-pulse"></div>
        ) : (
          <>
            <span className="text-3xl font-bold text-gray-100">{value}</span>
            <span className="text-sm text-gray-500 font-medium">{unit}</span>
          </>
        )}
      </div>

      {!loading && trend && (
        <div className="flex items-center gap-1 z-10 mt-1">
          {trend > 0 ? (
            <ArrowUp size={14} className="text-red-400" />
          ) : (
            <ArrowDown size={14} className="text-green-400" />
          )}
          <span className={`text-xs font-medium ${trend > 0 ? "text-red-400" : "text-green-400"}`}>
            {Math.abs(trend)}% from avg
          </span>
        </div>
      )}
    </div>
  );
}
