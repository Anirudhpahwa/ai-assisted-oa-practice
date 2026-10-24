const BASE = "/api";

function jsonHeaders(agent) {
  return { "Content-Type": "application/json", "X-Agent": agent };
}

async function handle(response) {
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.error || "Request failed");
  }
  return body;
}

export async function fetchReturns({ status, reason, q, sort = "newest", limit = 4, offset = 0 }) {
  const params = new URLSearchParams({ sort, limit, offset });
  if (status) params.set("status", status);
  if (reason) params.set("reason", reason);
  if (q) params.set("q", q);
  return handle(await fetch(`${BASE}/returns/?${params}`));
}

export async function fetchSummary(reason) {
  const params = new URLSearchParams();
  if (reason) params.set("reason", reason);
  return handle(await fetch(`${BASE}/returns/summary/?${params}`));
}

export async function createReturn(payload, agent) {
  return handle(
    await fetch(`${BASE}/returns/`, {
      method: "POST",
      headers: jsonHeaders(agent),
      body: JSON.stringify(payload),
    })
  );
}

export async function addItem(returnId, item, agent) {
  return handle(
    await fetch(`${BASE}/returns/${returnId}/items/`, {
      method: "POST",
      headers: jsonHeaders(agent),
      body: JSON.stringify(item),
    })
  );
}

export async function transitionReturn(returnId, to, agent) {
  return handle(
    await fetch(`${BASE}/returns/${returnId}/transition/`, {
      method: "POST",
      headers: jsonHeaders(agent),
      body: JSON.stringify({ to }),
    })
  );
}
