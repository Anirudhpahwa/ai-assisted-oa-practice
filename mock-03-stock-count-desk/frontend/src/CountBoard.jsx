import { useEffect, useState } from "react";
import { fetchSessions } from "./api";

const STATUSES = ["", "open", "submitted", "approved", "voided"];
const SORTS = ["scheduled", "scheduled_desc", "location"];
const PER_PAGE = 4;

export default function CountBoard() {
  const [filters, setFilters] = useState({ status: "", location: "", q: "", sort: "scheduled" });
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ results: [], total: 0, pages: 0 });
  const [error, setError] = useState("");

  useEffect(() => {
    fetchSessions({ ...filters, page, perPage: PER_PAGE })
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
      <h2>Count sessions</h2>
      <div className="filters">
        <select value={filters.status} onChange={(e) => updateFilter("status", e.target.value)}>
          {STATUSES.map((status) => (
            <option key={status} value={status}>
              {status || "any status"}
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
        <input
          placeholder="location"
          value={filters.location}
          onChange={(e) => updateFilter("location", e.target.value)}
        />
        <input placeholder="search" value={filters.q} onChange={(e) => updateFilter("q", e.target.value)} />
      </div>
      {error && <p className="error">{error}</p>}
      <ul>
        {data.results.map((session) => (
          <li key={session.id}>
            <strong>{session.location}</strong> {session.scheduled_for} · {session.assigned_to} ·{" "}
            {session.status} ({session.line_count} lines)
          </li>
        ))}
      </ul>
      <p>
        Page {page} of {data.pages} ({data.total} sessions)
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
