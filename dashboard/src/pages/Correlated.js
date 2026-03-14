import React, { useState, useEffect } from 'react';
import { correlatedIncidents } from '../api';

export default function Correlated({ apiBase }) {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = (runNow = false) => {
    setLoading(true);
    correlatedIncidents(runNow, 24, 50)
      .then(setList)
      .catch((e) => { setList([]); console.error(e); })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <h1 className="page-title">Correlated Incidents</h1>
      <div className="card">
        <p className="muted">Alerts grouped by time proximity, topology, and metric similarity to reduce noise.</p>
        <button className="btn primary" onClick={() => load(true)}>Run correlation now (last 24h)</button>
        {loading && <p>Loading...</p>}
        {!loading && (
          <div>
            {list.map((g) => (
              <div key={g.group_id} className="card" style={{ marginTop: '0.5rem' }}>
                <h4>Group #{g.group_id}</h4>
                <p><strong>Summary:</strong> {g.root_cause_summary}</p>
                <p><strong>Affected nodes:</strong> {g.affected_nodes?.join(', ') || '—'}</p>
                <p><strong>Incident IDs:</strong> {g.incident_ids?.join(', ') || '—'}</p>
                {g.created_at && <p className="muted">Created: {new Date(g.created_at).toLocaleString()}</p>}
              </div>
            ))}
            {list.length === 0 && <p className="muted">No correlated groups. Click &quot;Run correlation now&quot; or wait for automatic correlation.</p>}
          </div>
        )}
      </div>
    </div>
  );
}
