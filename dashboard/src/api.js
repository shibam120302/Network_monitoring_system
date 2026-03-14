const getBase = () => process.env.REACT_APP_API_URL || '';

export async function api(path, options = {}) {
  const base = getBase();
  const url = path.startsWith('http') ? path : `${base}/api/v1${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) throw new Error(await res.text());
  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

export function nodes() {
  return api('/nodes');
}

export function nodeMetrics(nodeId, hours = 24) {
  return api(`/metrics/nodes/${nodeId}/history?hours=${hours}`);
}

export function incidents(params = {}) {
  const q = new URLSearchParams(params).toString();
  return api(`/incidents${q ? '?' + q : ''}`);
}

export function incident(id) {
  return api(`/incidents/${id}`);
}

export function topology() {
  return api('/topology');
}

export function dailyReport(date, regenerate = false) {
  let q = '';
  if (date) q += `date=${encodeURIComponent(date)}`;
  if (regenerate) q += (q ? '&' : '') + 'regenerate=true';
  return api(`/reports/daily${q ? '?' + q : ''}`);
}

export function sla(nodeId, hours = 24) {
  let q = `hours=${hours}`;
  if (nodeId) q += `&node_id=${encodeURIComponent(nodeId)}`;
  return api(`/sla?${q}`);
}

export function chat(message) {
  return api('/ai/chat', { method: 'POST', body: JSON.stringify({ message }) });
}

export function simulate(type, nodeId) {
  return api(`/simulate/${type}`, {
    method: 'POST',
    body: JSON.stringify({ node_id: nodeId }),
  });
}
