import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Homepage from "./pages/Homepage";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";
import PatientDetail from "./pages/PatientDetail";
import PatientList from "./pages/PatientList";
import PredictionModels from "./pages/PredictionModels";
import Settings from "./pages/Settings";

function App() {
  return (
    <Routes>
      {/* Public pages — no sidebar layout */}
      <Route path="/" element={<Homepage />} />
      <Route path="/login" element={<Login />} />

      {/* App pages — inside sidebar Layout */}
      <Route element={<Layout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/patients" element={<PatientList />} />
        <Route path="/patients/:id" element={<PatientDetail />} />
        <Route path="/models" element={<PredictionModels />} />
        <Route path="/settings" element={<Settings />} />
      </Route>

      {/* 404 catch-all */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export default App;
