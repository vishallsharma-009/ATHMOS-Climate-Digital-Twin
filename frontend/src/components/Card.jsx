export default function Card({ title, children }) {
  return (
    <div className="bg-twin-panel border border-gray-800 rounded-lg p-4">
      {title && (
        <h3 className="text-sm text-gray-400 mb-2 uppercase tracking-wide">
          {title}
        </h3>
      )}
      {children}
    </div>
  );
}
