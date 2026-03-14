import React, { useState, useEffect } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import { Line } from 'react-chartjs-2';
import { nodes, incidents, nodeMetrics } from '../api';
import './Dashboard.css';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

export default function Dashboard({ apiBase }) {
  const [nodeList, setNodeList] = useState([]);
  const [incidentList, setIncidentList] = useState([]);
  const [latencyData, setLatencyData] = useState({ labels: [], datasets: [] });
  const [packetLossData, setPacketLossData] = useState({ labels: [], datasets: [] });
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [n, i] = await Promise.all([nodes(), incidents({ limit: 20 })]);
        if (!cancelled) {
          setNodeList(n);
          setIncidentList(i);
        }
      } catch (e) {
        if (!cancelled) console.error(e);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!selectedNode) {
      setLatencyData({ labels: [], datasets: [] });
      setPacketLossData({ labels: [], datasets: [] });
      return;
    }
    let cancelled = false;
    nodeMetrics(selectedNode, 24).then((metrics) => {
      if (cancelled || !metrics.length) return;
      const sorted = [...metrics].reverse();
      const labels = sorted.map((m) => new Date(m.timestamp).toLocaleTimeString());
      setLatencyData({
        labels,
        datasets: [{ label: 'Latency (ms)', data: sorted.map((m) => m.latency_ms), borderColor: '#38bdf8', tension: 0.3 }],
      });
      setPacketLossData({
        labels,
        datasets: [{ label: 'Packet loss (%)', data: sorted.map((m) => m.packet_loss_pct), borderColor: '#f87171', tension: 0.3 }],
      });
    }).catch(() => {});
    return () => { cancelled = true; };
  }, [selectedNode]);

  const up = nodeList.filter((n) => n.status === 'up').length;
  const down = nodeList.filter((n) => n.status === 'down').length;
  const degraded = nodeList.filter((n) => n.status === 'degraded').length;
  const openIncidents = incidentList.filter((i) => ['open', 'investigating', 'remediating'].includes(i.status));

  if (loading) return <div className="page-title">Loading...</div>;

  return (
    <div className="dashboard">
      <h1 className="page-title">Dashboard</h1>

      <div className="stats-row">
        <div className="stat-card">
          <span className="stat-value">{nodeList.length}</span>
          <span className="stat-label">Total Nodes</span>
        </div>
        <div className="stat-card up">
          <span className="stat-value">{up}</span>
          <span className="stat-label">Up</span>
        </div>
        <div className="stat-card degraded">
          <span className="stat-value">{degraded}</span>
          <span className="stat-label">Degraded</span>
        </div>
        <div className="stat-card down">
          <span className="stat-value">{down}</span>
          <span className="stat-label">Down</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{openIncidents.length}</span>
          <span className="stat-label">Active Incidents</span>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="card">
          <h3>Latency (select node)</h3>
          <select value={selectedNode || ''} onChange={(e) => setSelectedNode(e.target.value || null)}>
            <option value="">-- Select node --</option>
            {nodeList.slice(0, 30).map((n) => (
              <option key={n.node_id} value={n.node_id}>{n.node_id}</option>
            ))}
          </select>
          {latencyData.datasets.length > 0 && (
            <div className="chart-wrap">
              <Line data={latencyData} options={{ responsive: true, scales: { y: { beginAtZero: true } } }} />
            </div>
          )}
        </div>
        <div className="card">
          <h3>Packet loss (same node)</h3>
          {packetLossData.datasets.length > 0 && (
            <div className="chart-wrap">
              <Line data={packetLossData} options={{ responsive: true, scales: { y: { beginAtZero: true } } }} />
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <h3>Active Incidents</h3>
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Node</th>
              <th>Issue</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {openIncidents.slice(0, 10).map((i) => (
              <tr key={i.incident_id}>
                <td><a href={`#/incidents/${i.incident_id}`}>{i.incident_id}</a></td>
                <td>{i.node_node_id || i.node_id}</td>
                <td>{i.issue_type}</td>
                <td>{i.severity}</td>
                <td><span className={`status-badge ${i.status}`}>{i.status}</span></td>
                <td>{new Date(i.timestamp).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {openIncidents.length === 0 && <p className="muted">No active incidents.</p>}
      </div>
    </div>
  );
}
