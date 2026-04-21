const BASE = '/api';

export async function fetchDashboard() {
  const res = await fetch(`${BASE}/dashboard`);
  return res.json();
}

export async function fetchSession(name) {
  const res = await fetch(`${BASE}/session/${name}`);
  return res.json();
}

export async function fetchProblem(sessionName, slot) {
  const res = await fetch(`${BASE}/problem/${sessionName}/${slot}`);
  return res.json();
}

export async function startSession(data) {
  const res = await fetch(`${BASE}/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function saveCode(filepath, code, notes) {
  const res = await fetch(`${BASE}/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filepath, code, notes }),
  });
  return res.json();
}

export async function runTests(filepath, code, notes) {
  const res = await fetch(`${BASE}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filepath, code, notes }),
  });
  return res.json();
}

export async function fetchFromUrl(filepath, url) {
  const res = await fetch(`${BASE}/fetch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filepath, url }),
  });
  return res.json();
}
