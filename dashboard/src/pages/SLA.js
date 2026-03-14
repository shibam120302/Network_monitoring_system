import React, { useState, useEffect } from 'react';
import { sla } from '../api';

export default function SLA({ apiBase }) {
  const [data, setData] = useState([]);
  const [hours, setHours] = useState(24);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    sla(null, hours)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [hours]);

  if (loading) return <div className="page-title">Loading...</div>;

  const row = data[0];
  return (
    <div>
      <h1 className="page-title">SLA Metrics</h1>
      <div className="card">
        <p>
          <label>Period: </label>
          <select value={hours} onChange={(e) => setHours(Number(e.target.value))}>
            <option value={24}>Last 24 hours</option>
            <option value={168}>Last 7 days</option>
            <option value={720}>Last 30 days</option>
          </select>
        </p>
        {row && (
          <table className="table">
            <thead>
              <tr>
                <th>Uptime %</th>
                <th>MTTR (min)</th>
                <th>MTBF (min)</th>
                <th>Incident count</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>{row.uptime_pct != null ? row.uptime_pct.toFixed(2) : 'N/A'}</td>
                <td>{row.mttr_minutes != null ? row.mttr_minutes.toFixed(2) : 'N/A'}</td>
                <td>{row.mtbf_minutes != null ? row.mtbf_minutes.toFixed(2) : 'N/A'}</td>
                <td>{row.incident_count}</td>
              </tr>
            </tbody>
          </table>
        )}
        {(!row || data.length === 0) && <p className="muted">No SLA data for this period.</p>}
      </div>
    </div>
  );
}
