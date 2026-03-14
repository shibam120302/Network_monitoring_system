import React, { useState, useEffect } from 'react';
import { nodes } from '../api';

export default function Nodes({ apiBase }) {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    nodes()
      .then(setList)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page-title">Loading...</div>;

  return (
    <div>
      <h1 className="page-title">Nodes</h1>
      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>Node ID</th>
              <th>Hostname</th>
              <th>IP</th>
              <th>Status</th>
              <th>Latency (ms)</th>
              <th>Packet loss (%)</th>
              <th>CPU (%)</th>
            </tr>
          </thead>
          <tbody>
            {list.map((n) => (
              <tr key={n.node_id}>
                <td><strong>{n.node_id}</strong></td>
                <td>{n.hostname || '-'}</td>
                <td>{n.ip_address || '-'}</td>
                <td><span className={`status-badge ${n.status}`}>{n.status}</span></td>
                <td>{n.latest_latency != null ? n.latest_latency.toFixed(1) : '-'}</td>
                <td>{n.latest_packet_loss != null ? n.latest_packet_loss.toFixed(1) : '-'}</td>
                <td>{n.latest_cpu != null ? n.latest_cpu.toFixed(1) : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {list.length === 0 && <p className="muted">No nodes. Run agents or seed data.</p>}
      </div>
    </div>
  );
}
