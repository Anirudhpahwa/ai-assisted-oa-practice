const { HttpError } = require("../errors");
const { ALL_STATUSES } = require("./eventValidator");

const DEFAULT_PAGE_SIZE = 10;
const MAX_PAGE_SIZE = 50;

function bad(message) {
  return new HttpError(400, message);
}

function parseWhole(raw, fallback, min, max, message) {
  if (raw === undefined || raw === "") return fallback;
  if (typeof raw !== "string" || !/^\d+$/.test(raw)) throw bad(message);
  const value = Number(raw);
  if (value < min || value > max) throw bad(message);
  return value;
}

function parseDate(raw, name) {
  if (raw === undefined || raw === "") return null;
  if (typeof raw !== "string" || Number.isNaN(Date.parse(raw))) {
    throw bad(`${name} must be a valid date`);
  }
  return new Date(raw);
}

/** Reads the query string of GET /api/events into typed filters and paging. */
function parseListParams(query) {
  const status = typeof query.status === "string" && query.status !== "" ? query.status : null;
  if (status !== null && !ALL_STATUSES.includes(status)) {
    throw bad("status must be draft, published or cancelled");
  }
  const from = parseDate(query.from, "from");
  const to = parseDate(query.to, "to");
  if (from && to && from > to) {
    throw bad("from must not be after to");
  }
  const q = typeof query.q === "string" ? query.q.trim() : "";
  return {
    status,
    q,
    from,
    to,
    page: parseWhole(query.page, 1, 1, Number.MAX_SAFE_INTEGER, "page must be a positive integer"),
    pageSize: parseWhole(
      query.limit,
      DEFAULT_PAGE_SIZE,
      1,
      MAX_PAGE_SIZE,
      "pageSize must be an integer from 1 to 50"
    ),
  };
}

module.exports = { parseListParams };
