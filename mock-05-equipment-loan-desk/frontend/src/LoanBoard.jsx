import { useEffect, useState } from "react";
import { fetchLoans } from "./api";

const STATUSES = ["", "active", "returned", "cancelled"];
const SORTS = ["due", "newest", "borrower"];
const PER_PAGE = 5;

export default function LoanBoard() {
  const [filters, setFilters] = useState({ status: "", borrower: "", q: "", overdueOn: "", sort: "due" });
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ results: [], total: 0, pages: 0 });
  const [error, setError] = useState("");

  useEffect(() => {
    fetchLoans({ ...filters, page, perPage: PER_PAGE })
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
      <h2>Loans</h2>
      <div className="filters">
        <select value={filters.status} onChange={(e) => updateFilter("status", e.target.value)}>
          {STATUSES.map((status) => (
            <option key={status} value={status}>
              {status || "any status"}
            </option>
          ))}
        </select>
        <input
          placeholder="Borrower"
          value={filters.borrower}
          onChange={(e) => updateFilter("borrower", e.target.value)}
        />
        <input placeholder="Search" value={filters.q} onChange={(e) => updateFilter("q", e.target.value)} />
        <input
          type="date"
          title="Overdue on"
          value={filters.overdueOn}
          onChange={(e) => updateFilter("overdueOn", e.target.value)}
        />
        <select value={filters.sort} onChange={(e) => updateFilter("sort", e.target.value)}>
          {SORTS.map((sort) => (
            <option key={sort} value={sort}>
              {sort}
            </option>
          ))}
        </select>
      </div>
      {error && <p role="alert">{error}</p>}
      <table>
        <thead>
          <tr>
            <th>Borrower</th>
            <th>Status</th>
            <th>Due</th>
            <th>Items</th>
            <th>Fee</th>
          </tr>
        </thead>
        <tbody>
          {data.results.map((loan) => (
            <tr key={loan.id}>
              <td>{loan.borrower}</td>
              <td>{loan.status}</td>
              <td>{loan.due_on}</td>
              <td>{loan.items.map((item) => `${item.quantity} x ${item.name}`).join(", ")}</td>
              <td>{(loan.fee_cents / 100).toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="pager">
        <button disabled={page <= 1} onClick={() => setPage(page - 1)}>
          Previous
        </button>
        <span>
          Page {data.page || page} of {data.pages} ({data.total} loans)
        </span>
        <button disabled={page >= data.pages} onClick={() => setPage(page + 1)}>
          Next
        </button>
      </div>
    </section>
  );
}
