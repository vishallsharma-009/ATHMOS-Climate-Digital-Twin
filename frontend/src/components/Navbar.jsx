export default function Navbar() {
  return (
    <header className="h-14 bg-twin-panel border-b border-gray-800 flex items-center px-6 justify-between">
      <div className="flex items-center gap-2">
        <span className="text-blue-400 font-bold">🌍</span>
        <span className="font-semibold tracking-wide">
          ATHMOS Climate Digital Twin
        </span>
      </div>
      <span className="text-xs text-gray-400">Pilot Region: Gujarat</span>
    </header>
  );
}
