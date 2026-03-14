import React, { useState, useEffect } from 'react';
import { chaosSimulate, chaosRuns } from '../api';

const FAILURE_TYPES = [
  { value: 'packet_loss', label: 'Packet loss' },
  { value: 'high_latency', label: 'High latency' },
  { value: 'cpu_spike', label: 'CPU spike' },
  { value: 'link_failure', label: 'Link failure' },
  { value: 'node_shutdown', label: 'Node shutdown' },
];

export default function Chaos({ apiBase }) {
  const [nodeId, setNodeId] = useState('node-1');
  const [failureType, setFailureType] = useState('packet_loss');
  const [result, setResult] = useState(null);
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(false);

  const runSimulation = () => {
    setLoading(true);
    setResult(null);
    chaosSimulate(nodeId, failureType, 120)
      .then(setResult)
      .catch((e) => setResult({ success: false, message: e.message }))
      .finally(() => {
        setLoading(false);
        chaosRuns().then(setRuns).catch(() => {});
      });
  };

  useEffect(() => {
    chaosRuns().then(setRuns).catch(() => {});
  }, []);

  return (
    <div>
      <h1 className="page-title">Chaos Engineering</h1>
      <div className="card">
        <p className="muted">Inject failures to test detection and self-healing. Verify detection and remediation workflows.</p>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center', marginBottom: '1rem' }}>
          <label>Node ID:</label>
          <input type="text" className="input" value={nodeId} onChange={(e) => setNodeId(e.target.value)} placeholder="node-1" />
          <label>Failure type:</label>
          <select className="input" value={failureType} onChange={(e) => setFailureType(e.target.value)}>
            {FAILURE_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
          <button className="btn primary" onClick={runSimulation} disabled={loading}>
            {loading ? 'Running...' : 'Run chaos simulation'}
          </button>
        </div>
        {result && (
          <div className={result.success ? 'success' : 'error'} style={{ marginTop: '0.5rem' }}>
            {result.message}
            {result.detection_verified != null && (
              <span> — Detection: {result.detection_verified ? 'Yes' : 'No'}, Remediation: {result.remediation_verified ? 'Yes' : 'No'}</span>
            )}
          </div>
        )}
      </div>
      <div className="card">
        <h3>Recent chaos runs</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Run ID</th>
              <th>Node</th>
              <th>Failure type</th>
              <th>Started</th>
              <th>Detection</th>
              <th>Remediation</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((r) => (
              <tr key={r.id}>
                <td>{r.id}</td>
                <td>{r.node_id}</td>
                <td>{r.failure_type}</td>
                <td>{r.started_at ? new Date(r.started_at).toLocaleString() : '—'}</td>
                <td>{r.detection_verified == null ? '—' : r.detection_verified ? 'Yes' : 'No'}</td>
                <td>{r.remediation_verified == null ? '—' : r.remediation_verified ? 'Yes' : 'No'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {runs.length === 0 && <p className="muted">No chaos runs yet.</p>}
      </div>
    </div>
  );
}
