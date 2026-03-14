import React from 'react';
import { HashRouter, Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Nodes from './pages/Nodes';
import Incidents from './pages/Incidents';
import Topology from './pages/Topology';
import Reports from './pages/Reports';
import Chat from './pages/Chat';
import SLA from './pages/SLA';
import Simulate from './pages/Simulate';
import './App.css';

const API_BASE = process.env.REACT_APP_API_URL || '';

function App() {
  return (
    <HashRouter>
      <nav className="nav">
        <div className="nav-brand">Network Monitor</div>
        <div className="nav-links">
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/nodes">Nodes</NavLink>
          <NavLink to="/incidents">Incidents</NavLink>
          <NavLink to="/topology">Topology</NavLink>
          <NavLink to="/reports">Reports</NavLink>
          <NavLink to="/sla">SLA</NavLink>
          <NavLink to="/chat">AI Chat</NavLink>
          <NavLink to="/simulate">Simulate</NavLink>
        </div>
      </nav>
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard apiBase={API_BASE} />} />
          <Route path="/nodes" element={<Nodes apiBase={API_BASE} />} />
          <Route path="/incidents" element={<Incidents apiBase={API_BASE} />} />
          <Route path="/topology" element={<Topology apiBase={API_BASE} />} />
          <Route path="/reports" element={<Reports apiBase={API_BASE} />} />
          <Route path="/sla" element={<SLA apiBase={API_BASE} />} />
          <Route path="/chat" element={<Chat apiBase={API_BASE} />} />
          <Route path="/simulate" element={<Simulate apiBase={API_BASE} />} />
        </Routes>
      </main>
    </HashRouter>
  );
}

export default App;
