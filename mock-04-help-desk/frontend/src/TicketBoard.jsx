import { useEffect, useState } from "react";
import { fetchTickets } from "./api";

const STATUSES = ["", "open", "in_progress", "waiting", "resolved", "closed"];
const PRIORITIES = ["", "low", "normal", "high", "urgent"];
const SORTS = ["newest", "due", "priority"];
const PER_PAGE = 5;

export default function TicketBoard() {
  const [filters, setFilters] = useState({ status: "", priority: "", q: "", overdue: false, sort: "newest" });
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ results: [], total: 0, pages: 0 });
  const [error, setError] = useState("");

  useEffect(() => {
    fetchTickets({ ...filters, page, perPage: PER_PAGE })
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
      <h2>Tickets</h2>
      <div className="filters">
        <select value={filters.status} onChange={(e) => updateFilter("status", e.target.value)}>
          {STATUSES.map((status) => (
            <option key={status} value={status}>
              {status || "any status"}
            </option>
          ))}
        </select>
        <select value={filters.priority} onChange={(e) => updateFilter("priority", e.target.value)}>
          {PRIORITIES.map((priority) => (
            <option key={priority} value={priority}>
              {priority || "any priority"}
            </option>
          ))}
        </select>
        <select value={filters.sort} onChange={(e) => updateFilter("sort", e.target.value)}>
          {SORTS.map((sort) => (
            <option key={sort} value={sort}>
              {sort}
            </option>
          ))}
        </select>
        <input placeholder="search" value={filters.q} onChange={(e) => updateFilter("q", e.target.value)} />
        <label>
          <input
            type="checkbox"
            checked={filters.overdue}
            onChange={(e) => updateFilter("overdue", e.target.checked)}
          />
          overdue only
        </label>
      </div>
      {error && <p className="error">{error}</p>}
      <ul>
        {data.results.map((ticket) => (
          <li key={ticket.id}>
            <strong>{ticket.title}</strong> {ticket.priority} · {ticket.status} ·{" "}
            {ticket.assignee || "unassigned"} · due {ticket.due_at}
          </li>
        ))}
      </ul>
      <p>
        Page {page} of {data.pages} ({data.total} tickets)
      </p>
      <button disabled={page <= 1} onClick={() => setPage(page - 1)}>
        Previous
      </button>
      <button disabled={page >= data.pages} onClick={() => setPage(page + 1)}>
        Next
      </button>
    </section>
  );
}
