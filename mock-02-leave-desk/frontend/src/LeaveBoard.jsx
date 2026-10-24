import { useEffect, useState } from "react";
import { fetchLeave } from "./api";

const STATUSES = ["", "pending", "approved", "rejected", "cancelled"];
const TYPES = ["", "annual", "sick", "unpaid"];
const PER_PAGE = 5;

export default function LeaveBoard() {
  const [filters, setFilters] = useState({ status: "", leaveType: "", department: "" });
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ results: [], total: 0, pages: 0 });
  const [error, setError] = useState("");

  useEffect(() => {
    fetchLeave({ ...filters, page, perPage: PER_PAGE })
      .then((body) => {
        setData(body);
        setError("");
      })
      .catch((err) => setError(err.message));
  }, [filters, page]);

  function updateFilter(name, value) {
    setFilters((current) => ({ ...current, [name]: value }));
    setPage(1);
  }

  return (
    <section>
      <h2>Leave requests</h2>
      <div className="filters">
        <select value={filters.status} onChange={(e) => updateFilter("status", e.target.value)}>
          {STATUSES.map((status) => (
            <option key={status} value={status}>
              {status || "any status"}
            </option>
          ))}
        </select>
        <select value={filters.leaveType} onChange={(e) => updateFilter("leaveType", e.target.value)}>
          {TYPES.map((type) => (
            <option key={type} value={type}>
              {type || "any type"}
            </option>
          ))}
        </select>
        <input
          placeholder="department"
          value={filters.department}
          onChange={(e) => updateFilter("department", e.target.value)}
        />
      </div>
      {error && <p className="error">{error}</p>}
      <ul>
        {data.results.map((leave) => (
          <li key={leave.id}>
            <strong>{leave.employee_name}</strong> {leave.leave_type} {leave.start_date} to{" "}
            {leave.end_date} ({leave.days} days) · {leave.status}
          </li>
        ))}
      </ul>
      <div className="pager">
        <button disabled={page <= 1} onClick={() => setPage(page - 1)}>
          Previous
        </button>
        <span>
          Page {page} of {data.pages} ({data.total} requests)
        </span>
        <button disabled={page >= data.pages} onClick={() => setPage(page + 1)}>
          Next
        </button>
      </div>
    </section>
  );
}
