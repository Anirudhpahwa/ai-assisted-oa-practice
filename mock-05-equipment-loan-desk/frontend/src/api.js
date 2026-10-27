const BASE = "/api";

function jsonHeaders(user) {
  return { "Content-Type": "application/json", "X-Clerk": user };
}

async function handle(response) {
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.error || "Request failed");
  }
  return body;
}

function send(path, payload, user) {
  return fetch(`${BASE}${path}`, {
    method: "POST",
    headers: jsonHeaders(user),
    body: JSON.stringify(payload),
  }).then(handle);
}

export async function fetchLoans({
  status,
  borrower,
  equipment,
  q,
  dueFrom,
  dueTo,
  overdueOn,
  sort = "due",
  page = 1,
  perPage = 5,
}) {
  const params = new URLSearchParams({ sort, page, per_page: perPage });
  if (status) params.set("status", status);
  if (borrower) params.set("borrower", borrower);
  if (equipment) params.set("equipment", equipment);
  if (q) params.set("q", q);
  if (dueFrom) params.set("due_from", dueFrom);
  if (dueTo) params.set("due_to", dueTo);
  if (overdueOn) params.set("overdue_on", overdueOn);
  return handle(await fetch(`${BASE}/loans/?${params}`));
}

export async function fetchLoan(loanId) {
  return handle(await fetch(`${BASE}/loans/${loanId}/`));
}

export async function fetchSummary(from, to) {
  return handle(await fetch(`${BASE}/summary/?from=${from}&to=${to}`));
}

export function createLoan(borrower, start, items, user) {
  return send("/loans/", { borrower, start, items }, user);
}

export function returnLoan(loanId, returnedOn, user) {
  return send(`/loans/${loanId}/return/`, { returned_on: returnedOn }, user);
}

export function extendLoan(loanId, days, user) {
  return send(`/loans/${loanId}/extend/`, { days }, user);
}

export function cancelLoan(loanId, user) {
  return send(`/loans/${loanId}/cancel/`, {}, user);
}
