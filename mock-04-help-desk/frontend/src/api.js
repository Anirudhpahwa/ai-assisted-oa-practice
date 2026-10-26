const BASE = "/api";

function jsonHeaders(user, extra = {}) {
  return { "Content-Type": "application/json", "X-Agent": user, ...extra };
}

async function handle(response) {
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.error || "Request failed");
  }
  return body;
}

function send(method, path, payload, user, extraHeaders) {
  return fetch(`${BASE}${path}`, {
    method,
    headers: jsonHeaders(user, extraHeaders),
    body: JSON.stringify(payload),
  }).then(handle);
}

export async function fetchTickets({
  status,
  priority,
  assignee,
  requester,
  q,
  createdFrom,
  createdTo,
  overdue,
  sort = "newest",
  page = 1,
  perPage = 5,
}) {
  const params = new URLSearchParams({ sort, page, per_page: perPage });
  if (status) params.set("status", status);
  if (priority) params.set("priority", priority);
  if (assignee) params.set("assignee", assignee);
  if (requester) params.set("requester", requester);
  if (q) params.set("q", q);
  if (createdFrom) params.set("created_from", createdFrom);
  if (createdTo) params.set("created_to", createdTo);
  if (overdue) params.set("overdue", "true");
  return handle(await fetch(`${BASE}/tickets/?${params}`));
}

export async function fetchTicket(ticketId) {
  return handle(await fetch(`${BASE}/tickets/${ticketId}/`));
}

export async function fetchReport(from, to) {
  return handle(await fetch(`${BASE}/report/?from=${from}&to=${to}`));
}

export function createTicket(payload, user, idempotencyKey) {
  const extra = idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {};
  return send("POST", "/tickets/", payload, user, extra);
}

export function updateTicket(ticketId, changes, user) {
  return send("PATCH", `/tickets/${ticketId}/`, changes, user);
}

export function changeStatus(ticketId, status, user) {
  return send("POST", `/tickets/${ticketId}/status/`, { status }, user);
}

export function addComment(ticketId, body, internal, user) {
  return send("POST", `/tickets/${ticketId}/comments/`, { body, internal }, user);
}
