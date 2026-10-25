const BASE = "/api";

function jsonHeaders(user) {
  return { "Content-Type": "application/json", "X-Staff": user };
}

async function handle(response) {
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.error || "Request failed");
  }
  return body;
}

function post(path, payload, user) {
  return fetch(`${BASE}${path}`, {
    method: "POST",
    headers: jsonHeaders(user),
    body: JSON.stringify(payload),
  }).then(handle);
}

export async function fetchSessions({
  status,
  location,
  assignedTo,
  scheduledFrom,
  scheduledTo,
  q,
  sort = "scheduled",
  page = 1,
  perPage = 4,
}) {
  const params = new URLSearchParams({ sort, page, per_page: perPage });
  if (status) params.set("status", status);
  if (location) params.set("location", location);
  if (assignedTo) params.set("assigned_to", assignedTo);
  if (scheduledFrom) params.set("scheduled_from", scheduledFrom);
  if (scheduledTo) params.set("scheduled_to", scheduledTo);
  if (q) params.set("q", q);
  return handle(await fetch(`${BASE}/sessions/?${params}`));
}

export async function fetchSession(sessionId) {
  return handle(await fetch(`${BASE}/sessions/${sessionId}/`));
}

export async function fetchSummary(from, to) {
  return handle(await fetch(`${BASE}/summary/?from=${from}&to=${to}`));
}

export function createSession(payload, user) {
  return post("/sessions/", payload, user);
}

export function recordCount(sessionId, sku, counted, user) {
  return post(`/sessions/${sessionId}/lines/`, { sku, counted }, user);
}

export function submitSession(sessionId, user) {
  return post(`/sessions/${sessionId}/submit/`, {}, user);
}

export function approveSession(sessionId, user) {
  return post(`/sessions/${sessionId}/approve/`, {}, user);
}

export function voidSession(sessionId, user) {
  return post(`/sessions/${sessionId}/void/`, {}, user);
}
