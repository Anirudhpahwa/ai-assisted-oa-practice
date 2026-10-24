import { useEffect, useState } from "react";
import { fetchReturns } from "./api";

const STATUSES = ["", "requested", "approved", "received", "refunded", "rejected", "cancelled"];
const REASONS = ["", "damaged", "wrong_item", "not_needed", "other"];
const SORTS = [
  ["newest", "Newest first"],
  ["oldest", "Oldest first"],
  ["refund_desc", "Highest refund"],
];
const PAGE_SIZE = 4;

function formatCents(cents) {
  return `$${(cents / 100).toFixed(2)}`;
}

export default function ReturnsList() {
  const [filters, setFilters] = useState({ status: "", reason: "", q: "", sort: "newest" });
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState({ results: [], total: 0, has_more: false });
  const [error, setError] = useState("");

  useEffect(() => {
    fetchReturns({ ...filters, limit: PAGE_SIZE, offset })
      .then((body) => {
        setData(body);
        setError("");
      })
      .catch((err) => setError(err.message));
  }, [filters, offset]);

  function updateFilter(name, value) {
    setFilters((current) => ({ ...current, [name]: value }));
    setOffset(0);
  }

  return (
    <section>
      <h2>Returns</h2>
      <div className="filters">
        <select value={filters.status} onChange={(e) => updateFilter("status", e.target.value)}>
          {STATUSES.map((status) => (
            <option key={status} value={status}>
              {status || "active statuses"}
            </option>
          ))}
        </select>
        <select value={filters.reason} onChange={(e) => updateFilter("reason", e.target.value)}>
          {REASONS.map((reason) => (
            <option key={reason} value={reason}>
              {reason || "any reason"}
            </option>
          ))}
        </select>
        <input
          placeholder="search customer, order or note"
          value={filters.q}
          onChange={(e) => updateFilter("q", e.target.value)}
        />
        <select value={filters.sort} onChange={(e) => updateFilter("sort", e.target.value)}>
          {SORTS.map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>
      {error && <p className="error">{error}</p>}
      <ul>
        {data.results.map((ret) => (
          <li key={ret.id}>
            <strong>{ret.order_number}</strong> {ret.customer} · {ret.status} ·{" "}
            {formatCents(ret.refund_total_cents)}
          </li>
        ))}
      </ul>
      <div className="pager">
        <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>
          Previous
        </button>
        <span>
          {data.total} returns, showing from {offset + 1}
        </span>
        <button disabled={!data.has_more} onClick={() => setOffset(offset + PAGE_SIZE)}>
          Next
        </button>
      </div>
    </section>
  );
}
