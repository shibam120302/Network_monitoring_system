import React, { useState } from 'react';
import { simulate } from '../api';

export default function Simulate({ apiBase }) {
  const [nodeId, setNodeId] = useState('node-1');
  const [result, setResult] = useState(null);

  const run = async (type) => {
    setResult(null);
    try {
      const res = await simulate(type, nodeId);
      setResult(res);
    } catch (e) {
      setResult({ success: false, message: e.message });
    }
  };

  return (
    <div>
      <h1 className="page-title">Failure Simulation</h1>
      <div className="card">
        <p className="muted">Inject artificial failures to test detection and remediation.</p>
        <p>
          <label>Node ID: </label>
          <input
            type="text"
            value={nodeId}
            onChange={(e) => setNodeId(e.target.value)}
            className="input"
            placeholder="node-1"
          />
        </p>
        <div className="simulate-buttons">
          <button className="btn" onClick={() => run('latency')}>Simulate latency spike</button>
          <button className="btn" onClick={() => run('packet_loss')}>Simulate packet loss</button>
          <button className="btn" onClick={() => run('link_failure')}>Simulate link failure</button>
          <button className="btn" onClick={() => run('cpu_spike')}>Simulate CPU spike</button>
        </div>
        {result && (
          <p className={result.success ? 'success' : 'error'}>
            {result.message}
          </p>
        )}
      </div>
    </div>
  );
}
