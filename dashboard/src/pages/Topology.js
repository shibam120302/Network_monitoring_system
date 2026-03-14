import React, { useState, useEffect } from 'react';
import { topology } from '../api';
import './Topology.css';

export default function Topology({ apiBase }) {
  const [data, setData] = useState({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    topology()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page-title">Loading...</div>;

  return (
    <div>
      <h1 className="page-title">Network Topology</h1>
      <div className="card">
        <p className="muted">Node status and link health. Green = up, Yellow = degraded, Red = down.</p>
        <div className="topology-viz">
          {data.nodes.length === 0 && <p>No topology data. Add nodes and topology links.</p>}
          {data.nodes.length > 0 && (
            <svg viewBox="0 0 800 400" className="topology-svg">
              {data.edges.map((e, i) => {
                const src = data.nodes.find((n) => n.id === e.source);
                const tgt = data.nodes.find((n) => n.id === e.target);
                const si = data.nodes.indexOf(src);
                const ti = data.nodes.indexOf(tgt);
                const x1 = 100 + (si % 10) * 70;
                const y1 = 80 + Math.floor(si / 10) * 80;
                const x2 = 100 + (ti % 10) * 70;
                const y2 = 80 + Math.floor(ti / 10) * 80;
                return (
                  <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke={e.is_up ? '#334155' : '#f87171'} strokeWidth="2" />
                );
              })}
              {data.nodes.map((n, i) => {
                const x = 100 + (i % 10) * 70;
                const y = 80 + Math.floor(i / 10) * 80;
                const color = n.status === 'up' ? '#34d399' : n.status === 'down' ? '#f87171' : '#fbbf24';
                return (
                  <g key={n.id}>
                    <circle cx={x} cy={y} r="14" fill={color} stroke="#1e293b" strokeWidth="2" />
                    <text x={x} y={y + 28} textAnchor="middle" fontSize="10" fill="#94a3b8">{n.label || n.id}</text>
                  </g>
                );
              })}
            </svg>
          )}
        </div>
      </div>
    </div>
  );
}
