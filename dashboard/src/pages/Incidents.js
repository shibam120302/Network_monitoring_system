import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { incidents, incident, incidentRootCause } from '../api';

export default function Incidents({ apiBase }) {
  const { id } = useParams();
  const [list, setList] = useState([]);
  const [detail, setDetail] = useState(null);
  const [rootCause, setRootCause] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    incidents({ limit: 100 })
      .then(setList)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!id) return;
    incident(id)
      .then(setDetail)
      .catch(() => setDetail(null));
  }, [id]);

  useEffect(() => {
    if (!id) return;
    incidentRootCause(id)
      .then(setRootCause)
      .catch(() => setRootCause(null));
  }, [id]);

  if (loading) return <div className="page-title">Loading...</div>;

  return (
    <div>
      <h1 className="page-title">Incidents</h1>
      {detail ? (
        <div className="card">
          <h3>Incident: {detail.incident_id}</h3>
          <p><strong>Node:</strong> {detail.node_node_id || detail.node_id}</p>
          <p><strong>Issue:</strong> {detail.issue_type} · <strong>Severity:</strong> {detail.severity} · <strong>Status:</strong> {detail.status}</p>
          <p><strong>Time:</strong> {new Date(detail.timestamp).toLocaleString()}</p>
          {detail.resolved_at && <p><strong>Resolved:</strong> {new Date(detail.resolved_at).toLocaleString()}</p>}
          {rootCause && (
            <>
              <h4>Root cause analysis</h4>
              <p><strong>Root cause:</strong> {rootCause.root_cause}</p>
              {rootCause.affected_nodes && rootCause.affected_nodes.length > 0 && (
                <p><strong>Affected nodes:</strong> {rootCause.affected_nodes.join(', ')}</p>
              )}
            </>
          )}
          <h4>Timeline</h4>
          <ul className="timeline">
            {detail.timeline && detail.timeline.map((e) => (
              <li key={e.id}>
                <span className="timeline-time">{new Date(e.event_time).toLocaleTimeString()}</span>
                <span className="timeline-type">{e.event_type}</span>
                {e.message && <span className="timeline-msg">{e.message}</span>}
              </li>
            ))}
          </ul>
          <p><a href="#/incidents">← Back to list</a></p>
        </div>
      ) : (
        <div className="card">
          <table className="table">
            <thead>
              <tr>
                <th>Incident ID</th>
                <th>Node</th>
                <th>Issue</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {list.map((i) => (
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
          {list.length === 0 && <p className="muted">No incidents.</p>}
        </div>
      )}
    </div>
  );
}
