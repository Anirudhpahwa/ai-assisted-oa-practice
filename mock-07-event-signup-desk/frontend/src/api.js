const BASE = "/api/events";

async function handle(response) {
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.error || "Request failed");
  }
  return body;
}

function call(method, path, user, payload) {
  const headers = { "X-User-Id": user };
  const options = { method, headers };
  if (payload !== undefined) {
    headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(payload);
  }
  return fetch(`${BASE}${path}`, options).then(handle);
}

export function fetchEvents(user, { status, q, from, to, page = 1, pageSize = 5 } = {}) {
  const params = new URLSearchParams({ page, pageSize });
  if (status) params.set("status", status);
  if (q) params.set("q", q);
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  return call("GET", `/?${params}`, user);
}

export function createEvent(user, { title, location, startsAt, capacity, status }) {
  return call("POST", "/", user, { title, location, startsAt, capacity, status });
}

export function updateEvent(user, eventId, changes) {
  return call("PATCH", `/${eventId}`, user, changes);
}

export function fetchSummary(user, eventId) {
  return call("GET", `/${eventId}/summary`, user);
}

export function register(user, eventId, guests = 0) {
  return call("POST", `/${eventId}/registrations`, user, { guests });
}

export function cancelRegistration(user, eventId, registrationId) {
  return call("DELETE", `/${eventId}/registrations/${registrationId}`, user);
}
