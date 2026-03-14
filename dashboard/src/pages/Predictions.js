import React, { useState, useEffect } from 'react';
import { predictions } from '../api';

export default function Predictions({ apiBase }) {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const fetchPredictions = (doRecompute = false) => {
    setLoading(true);
    predictions(doRecompute, 30)
      .then(setList)
      .catch((e) => { setList([]); console.error(e); })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchPredictions(recompute);
  }, []);

  return (
    <div>
      <h1 className="page-title">Predictive Failure Detection</h1>
      <div className="card">
        <p className="muted">ML-predicted probability of node failure in the next 10–30 minutes (Isolation Forest / Random Forest).</p>
        <button className="btn" onClick={() => fetchPredictions(false)} disabled={loading}>Refresh</button>
        <button className="btn primary" style={{ marginLeft: '0.5rem' }} onClick={() => fetchPredictions(true)} disabled={loading}>Recompute (ML)</button>
        {loading && <p>Loading...</p>}
        {!loading && (
          <table className="table">
            <thead>
              <tr>
                <th>Node ID</th>
                <th>Failure probability</th>
                <th>Predicted issue</th>
              </tr>
            </thead>
            <tbody>
              {list.map((p) => (
                <tr key={p.node_id}>
                  <td><strong>{p.node_id}</strong></td>
                  <td>{(p.failure_probability * 100).toFixed(1)}%</td>
                  <td>{p.predicted_issue || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {!loading && list.length === 0 && <p className="muted">No predictions. Run with recompute or ensure nodes have metric history.</p>}
      </div>
    </div>
  );
}
