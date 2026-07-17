import React, { useEffect } from "react";
import { MapContainer, TileLayer, GeoJSON, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Helper component to auto-fit map to GeoJSON bounds
function MapBoundsController({ geoData }) {
  const map = useMap();
  
  useEffect(() => {
    if (geoData) {
      try {
        const layer = L.geoJSON(geoData);
        const bounds = layer.getBounds();
        if (bounds.isValid()) {
          map.fitBounds(bounds, { padding: [20, 20] });
        }
      } catch (err) {
        console.error("Failed to fit bounds", err);
      }
    }
  }, [geoData, map]);
  
  return null;
}

export default function MapView({ geoData }) {
  return (
    <div className="h-full w-full rounded-lg overflow-hidden border border-gray-800 relative">
      <MapContainer 
        center={[20, 78]} // Fallback center (India)
        zoom={4} 
        style={{ height: "100%", width: "100%", background: "#1f2937" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          className="map-tiles"
        />
        {geoData && (
          <React.Fragment>
            <MapBoundsController geoData={geoData} />
            <GeoJSON 
              key={geoData?.features?.[0]?.properties?.name || JSON.stringify(geoData).substring(0, 50)} // force re-render on new data
              data={geoData} 
              style={() => ({
                color: '#3b82f6',
                weight: 2,
                fillColor: '#3b82f6',
                fillOpacity: 0.1,
              })}
            />
          </React.Fragment>
        )}
      </MapContainer>
    </div>
  );
}
