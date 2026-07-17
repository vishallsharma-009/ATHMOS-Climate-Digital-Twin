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

export default function MapView({ geoData, overlayType = "rainfall" }) {
  
  const onEachFeature = (feature, layer) => {
    if (feature.properties) {
      const district = feature.properties.name || feature.properties.dtname || "Unknown District";
      // Mock district data based on overlay type for visual feedback
      const mockValue = Math.random() * 40;
      const unit = overlayType === "rainfall" ? "mm" : "°C";
      
      const tooltipContent = `
        <div style="text-align: left; padding: 2px;">
          <h4 style="font-weight: bold; margin: 0 0 4px 0; color: #fff;">${district}</h4>
          <p style="margin: 0; color: #cbd5e1; font-size: 12px;">Current ${overlayType}: <span style="color: #60a5fa; font-weight: bold;">${mockValue.toFixed(1)}${unit}</span></p>
          <p style="margin: 2px 0 0 0; color: #cbd5e1; font-size: 12px;">Confidence: <span style="color: #34d399; font-weight: bold;">${(80 + Math.random()*15).toFixed(1)}%</span></p>
        </div>
      `;
      layer.bindTooltip(tooltipContent, { sticky: true, className: "custom-tooltip" });
    }
  };

  const style = (feature) => {
    // Generate a color based on some random logic to simulate a heatmap for districts
    const val = Math.random();
    let color = "#3b82f6"; // default blue
    
    if (overlayType === "temperature") {
      color = val > 0.8 ? "#ef4444" : val > 0.4 ? "#f97316" : "#fcd34d";
    } else if (overlayType === "rainfall") {
      color = val > 0.7 ? "#1d4ed8" : val > 0.3 ? "#3b82f6" : "#93c5fd";
    }

    return {
      fillColor: color,
      weight: 1,
      opacity: 1,
      color: "#1e293b",
      fillOpacity: 0.6 + (Math.random() * 0.3)
    };
  };

  return (
    <div className="h-full w-full relative">
      <MapContainer 
        center={[20, 78]} 
        zoom={4} 
        style={{ height: "100%", width: "100%", background: "#0b0e14" }}
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CartoDB</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        {geoData && (
          <React.Fragment>
            <MapBoundsController geoData={geoData} />
            <GeoJSON 
              key={`${geoData?.features?.[0]?.properties?.name}-${overlayType}`}
              data={geoData} 
              style={style}
              onEachFeature={onEachFeature}
            />
          </React.Fragment>
        )}
      </MapContainer>
    </div>
  );
}
