import { useEffect, useState } from "react";
import { fetchEvents, fetchSummary, updateEvent } from "./api.js";

const STATUSES = ["", "draft", "published", "cancelled"];

export default function EventBoard({ user }) {
  const [filters, setFilters] = useState({ status: "", q: "", page: 1 });
  const [data, setData] = useState({ items: [], total: 0, totalPages: 0 });
  const [summaries, setSummaries] = useState({});
  const [error, setError] = useState("");

  useEffect(() => {
    fetchEvents(user, filters)
      .then((result) => {
        setData(result);
        setError("");
      })
      .catch((err) => setError(err.message));
  }, [user, filters]);

  function change(patch) {
    setFilters((current) => ({ ...current, page: 1, ...patch }));
  }

  async function showSummary(eventId) {
    const summary = await fetchSummary(user, eventId);
    setSummaries((current) => ({ ...current, [eventId]: summary }));
  }

  async function publish(eventId) {
    await updateEvent(user, eventId, { status: "published" });
    change({});
  }

  return (
    <section>
      <div className="filters">
        <select value={filters.status} onChange={(e) => change({ status: e.target.value })}>
          {STATUSES.map((status) => (
            <option key={status} value={status}>
              {status || "all open"}
            </option>
          ))}
        </select>
        <input
          placeholder="Search title"
          value={filters.q}
          onChange={(e) => change({ q: e.target.value })}
        />
      </div>
      {error && <p className="error">{error}</p>}
      <ul>
        {data.items.map((event) => (
          <li key={event.id}>
            <strong>{event.title}</strong> · {new Date(event.startsAt).toLocaleString()} ·{" "}
            {event.status} · {event.capacity} seats
            {event.status === "draft" && <button onClick={() => publish(event.id)}>Publish</button>}
            <button onClick={() => showSummary(event.id)}>Summary</button>
            {summaries[event.id] && (
              <span className="summary">
                {summaries[event.id].confirmedSeats}/{event.capacity} seats ({summaries[event.id].fillRate}
                %), {summaries[event.id].waitlistedCount} waiting
              </span>
            )}
          </li>
        ))}
      </ul>
      <p>
        Page {filters.page} of {data.totalPages || 1} · {data.total} events
      </p>
      <button disabled={filters.page <= 1} onClick={() => setFilters({ ...filters, page: filters.page - 1 })}>
        Previous
      </button>
      <button
        disabled={filters.page >= data.totalPages}
        onClick={() => setFilters({ ...filters, page: filters.page + 1 })}
      >
        Next
      </button>
    </section>
  );
}
