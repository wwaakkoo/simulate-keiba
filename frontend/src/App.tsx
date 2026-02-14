import { BrowserRouter, Route, Routes } from "react-router-dom";
import { RaceSimulator } from "./simulation";
import { Dashboard } from "./components/Dashboard";
import { RaceList } from "./components/RaceList";
import { RaceDetail } from "./components/RaceDetail";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/races" element={<RaceList />} />
        <Route path="/races/:raceId" element={<RaceDetail />} />
        <Route path="/simulation" element={<RaceSimulator />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
