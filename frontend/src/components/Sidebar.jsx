import { NavLink } from "react-router-dom";
import { 
  Home, 
  Map, 
  LineChart, 
  Sliders, 
  BrainCircuit, 
  BriefcaseMedical, 
  ActivitySquare, 
  Settings 
} from "lucide-react";

const links = [
  { to: "/", label: "Home", icon: Home },
  { to: "/twin", label: "Live Digital Twin", icon: Map },
  { to: "/forecast", label: "Forecast Lab", icon: LineChart },
  { to: "/scenario", label: "Scenario Engine", icon: Sliders },
  { to: "/explain", label: "Explainable AI", icon: BrainCircuit },
  { to: "/decision", label: "Decision Support", icon: BriefcaseMedical },
  { to: "/health", label: "System Health", icon: ActivitySquare },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-gray-900 border-r border-gray-800 p-4 flex flex-col gap-2 flex-shrink-0">
      <div className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 px-3">
        Command Center
      </div>
      {links.map((link) => (
        <NavLink
          key={link.to}
          to={link.to}
          end={link.to === "/"}
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${
              isActive
                ? "bg-blue-600/20 text-blue-400 border border-blue-500/30 font-medium shadow-[0_0_15px_rgba(59,130,246,0.15)]"
                : "text-gray-400 hover:bg-gray-800 hover:text-gray-200 border border-transparent"
            }`
          }
        >
          <link.icon size={18} className="opacity-80" />
          {link.label}
        </NavLink>
      ))}
    </aside>
  );
}
