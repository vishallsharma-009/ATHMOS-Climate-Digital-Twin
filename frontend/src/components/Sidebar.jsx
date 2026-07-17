import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Dashboard" },
  { to: "/forecast", label: "Forecast" },
  { to: "/scenario", label: "Scenario Simulator" },
];

export default function Sidebar() {
  return (
    <aside className="w-56 bg-twin-panel border-r border-gray-800 p-4 flex flex-col gap-1">
      {links.map((link) => (
        <NavLink
          key={link.to}
          to={link.to}
          end={link.to === "/"}
          className={({ isActive }) =>
            `px-3 py-2 rounded-md text-sm ${
              isActive
                ? "bg-twin-accent text-white"
                : "text-gray-300 hover:bg-gray-800"
            }`
          }
        >
          {link.label}
        </NavLink>
      ))}
    </aside>
  );
}
