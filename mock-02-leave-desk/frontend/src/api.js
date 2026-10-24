const BASE = "/api";

function jsonHeaders(user) {
  return { "Content-Type": "application/json", "X-User": user };
}

async function handle(response) {
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.error || "Request failed");
  }
  return body;
}

export async function fetchLeave({ employeeId, status, leaveType, department, page = 1, perPage = 5 }) {
  const params = new URLSearchParams({ page, per_page: perPage });
  if (employeeId) params.set("employee_id", employeeId);
  if (status) params.set("status", status);
  if (leaveType) params.set("leave_type", leaveType);
  if (department) params.set("department", department);
  return handle(await fetch(`${BASE}/leave/?${params}`));
}

export async function fetchOut(date) {
  return handle(await fetch(`${BASE}/leave/out/?date=${date}`));
}

export async function fetchSummary(year) {
  return handle(await fetch(`${BASE}/leave/summary/?year=${year}`));
}

export async function requestLeave(payload, user) {
  return handle(
    await fetch(`${BASE}/leave/`, {
      method: "POST",
      headers: jsonHeaders(user),
      body: JSON.stringify(payload),
    })
  );
}

export async function decideLeave(leaveId, decision, user) {
  return handle(
    await fetch(`${BASE}/leave/${leaveId}/decision/`, {
      method: "POST",
      headers: jsonHeaders(user),
      body: JSON.stringify({ decision }),
    })
  );
}

export async function cancelLeave(leaveId, user) {
  return handle(
    await fetch(`${BASE}/leave/${leaveId}/cancel/`, {
      method: "POST",
      headers: jsonHeaders(user),
      body: JSON.stringify({}),
    })
  );
}
