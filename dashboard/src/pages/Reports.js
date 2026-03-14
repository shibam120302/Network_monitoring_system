import React, { useState, useEffect } from 'react';
import { dailyReport } from '../api';

const apiBase = process.env.REACT_APP_API_URL || '';

export default function Reports({ apiBase: _ }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);

  const load = (regen = false) => {
    setLoading(true);
    dailyReport(null, regen)
      .then(setReport)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const downloadPdf = () => {
    const base = process.env.REACT_APP_API_URL || '';
    const url = `${base}/api/v1/reports/daily/download`;
    window.open(url, '_blank');
  };

  if (loading && !report) return <div className="page-title">Loading...</div>;

  return (
    <div>
      <h1 className="page-title">Daily Report</h1>
      <div className="card">
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
          <button className="btn" onClick={() => load(true)} disabled={regenerating || loading}>
            {regenerating || loading ? 'Loading...' : 'Regenerate report'}
          </button>
          <button className="btn primary" onClick={downloadPdf}>Download PDF</button>
        </div>
        {report && (
          <>
            <p><strong>Report date:</strong> {new Date(report.report_date).toLocaleDateString()}</p>
            <p><strong>Total incidents:</strong> {report.total_incidents}</p>
            <p><strong>Affected nodes:</strong> {report.affected_nodes_count}</p>
            <p><strong>Avg downtime (min):</strong> {report.avg_downtime_minutes != null ? report.avg_downtime_minutes.toFixed(1) : 'N/A'}</p>
            <p><strong>Remediation success rate (%):</strong> {report.remediation_success_rate != null ? report.remediation_success_rate.toFixed(1) : 'N/A'}</p>
            <p><strong>Network health score:</strong> {report.network_health_score != null ? report.network_health_score.toFixed(0) : 'N/A'}/100</p>
            {report.ai_summary && (
              <div className="report-summary">
                <h4>AI Summary</h4>
                <p>{report.ai_summary}</p>
              </div>
            )}
          </>
        )}
        {!report && !loading && <p className="muted">No report yet. Click Regenerate to generate.</p>}
      </div>
    </div>
  );
}
