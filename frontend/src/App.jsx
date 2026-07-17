import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import { ClimateProvider } from "./context/ClimateContext";

// Pages
import Home from "./pages/Home";
import LiveDigitalTwin from "./pages/LiveDigitalTwin";
import ForecastLab from "./pages/ForecastLab";
import ScenarioEngine from "./pages/ScenarioEngine";
import ExplainableAI from "./pages/ExplainableAI";
import DecisionSupport from "./pages/DecisionSupport";
import SystemHealth from "./pages/SystemHealth";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <ClimateProvider>
      <div className="min-h-screen bg-[#0b0e14] text-gray-200 flex flex-col font-sans overflow-hidden">
        <Header />
        <div className="flex flex-1 overflow-hidden">
          <Sidebar />
          <main className="flex-1 overflow-y-auto overflow-x-hidden bg-[#0b0e14] p-4 relative">
            <div className="absolute inset-0 bg-grid-pattern opacity-[0.03] pointer-events-none"></div>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/twin" element={<LiveDigitalTwin />} />
              <Route path="/forecast" element={<ForecastLab />} />
              <Route path="/scenario" element={<ScenarioEngine />} />
              <Route path="/explain" element={<ExplainableAI />} />
              <Route path="/decision" element={<DecisionSupport />} />
              <Route path="/health" element={<SystemHealth />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>
        </div>
      </div>
    </ClimateProvider>
  );
}
