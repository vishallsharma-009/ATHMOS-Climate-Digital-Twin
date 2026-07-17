import { createContext, useContext, useEffect, useState } from "react";
import { api } from "../api";

const ClimateContext = createContext();

export function ClimateProvider({ children }) {
  const [dashboard, setDashboard] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [explain, setExplain] = useState(null);
  const [regions, setRegions] = useState([]);
  const [geoJsonData, setGeoJsonData] = useState(null);
  const [selectedRegion, setSelectedRegion] = useState("gujarat");
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      const [dashRes, foreRes, expRes, regsRes] = await Promise.all([
        api.getDashboard().catch(() => null),
        api.getForecast().catch(() => null),
        api.getExplain().catch(() => null),
        api.getRegions().catch(() => ["gujarat"])
      ]);
      
      if (dashRes) setDashboard(dashRes);
      if (foreRes) setForecast(foreRes.forecast);
      if (expRes) setExplain(expRes);
      if (regsRes) {
        setRegions(regsRes);
        if (regsRes.length > 0 && !selectedRegion) setSelectedRegion(regsRes[0]);
      }
      
      setLastUpdated(new Date());
    } catch (err) {
      console.error("Context initial fetch error", err);
      setError("Failed to connect to Digital Twin.");
    } finally {
      setLoading(false);
    }
  };

  const pollDashboardData = async () => {
    try {
      const dashRes = await api.getDashboard();
      setDashboard(dashRes);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      console.error("Polling error", err);
      // Optional: don't clear data, just show an error toast or offline indicator
      setError("Live data sync lost.");
    }
  };

  useEffect(() => {
    fetchInitialData();
    // Poll every 30 seconds
    const interval = setInterval(pollDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedRegion) {
      api.getGeojson(selectedRegion)
        .then(data => setGeoJsonData(data))
        .catch(err => console.error("Failed to load geojson", err));
    }
  }, [selectedRegion]);

  const value = {
    dashboard,
    forecast,
    explain,
    regions,
    geoJsonData,
    selectedRegion,
    setSelectedRegion,
    loading,
    error,
    lastUpdated,
    refreshAll: fetchInitialData
  };

  return (
    <ClimateContext.Provider value={value}>
      {children}
    </ClimateContext.Provider>
  );
}

export function useClimateData() {
  return useContext(ClimateContext);
}
