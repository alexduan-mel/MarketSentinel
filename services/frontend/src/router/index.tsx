import { Navigate, Route, Routes } from "react-router-dom";

import MonitorPage from "../pages/Monitor";
import SignalsPage from "../pages/Signals";
import TopicsPage from "../pages/Topics";
import BacktestPage from "../pages/Backtest";
import SystemPage from "../pages/System";

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<MonitorPage />} />
      <Route path="/signals" element={<SignalsPage />} />
      <Route path="/topics" element={<TopicsPage />} />
      <Route path="/backtest" element={<BacktestPage />} />
      <Route path="/system" element={<SystemPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
