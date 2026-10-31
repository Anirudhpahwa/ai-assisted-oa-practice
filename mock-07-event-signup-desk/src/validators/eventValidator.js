const { HttpError } = require("../errors");

const DEFAULT_CAPACITY = 25;
const MAX_CAPACITY = 500;
const CREATE_STATUSES = ["draft", "published"];
const ALL_STATUSES = ["draft", "published", "cancelled"];
const UPDATE_FIELDS = ["title", "location", "startsAt", "capacity", "status"];

function bad(message) {
  return new HttpError(400, message);
}

function checkTitle(value) {
  const title = typeof value === "string" ? value.trim() : "";
  if (title.length < 3 || title.length > 80) {
    throw bad("title must be 3 to 80 characters");
  }
  return title;
}

function checkLocation(value) {
  const location = typeof value === "string" ? value.trim() : null;
  if (location === null || location.length > 120) {
    throw bad("location must be at most 120 characters");
  }
  return location;
}

function checkStartsAt(value) {
  if (typeof value !== "string" || Number.isNaN(Date.parse(value))) {
    throw bad("startsAt must be a valid date");
  }
  return new Date(value);
}

function checkCapacity(value) {
  if (!Number.isInteger(value) || value < 1 || value > MAX_CAPACITY) {
    throw bad("capacity must be an integer from 1 to 500");
  }
  return value;
}

function checkStatus(value, allowed) {
  if (!allowed.includes(value)) {
    throw bad(`status must be ${allowed.slice(0, -1).join(", ")} or ${allowed[allowed.length - 1]}`);
  }
  return value;
}

function asObject(body) {
  return body && typeof body === "object" ? body : {};
}

/** Validates a create body and fills in defaults. */
function normalizeCreate(body) {
  const input = asObject(body);
  return {
    title: checkTitle(input.title),
    location: input.location === undefined ? "" : checkLocation(input.location),
    startsAt: checkStartsAt(input.startsAt),
    capacity: input.capacity === undefined ? DEFAULT_CAPACITY : checkCapacity(input.capacity),
    status: input.status === undefined ? "draft" : checkStatus(input.status, CREATE_STATUSES),
  };
}

/** Validates the fields present in an update body; absent fields are left out. */
function normalizeUpdate(body) {
  const input = asObject(body);
  if (!UPDATE_FIELDS.some((field) => input[field] !== undefined)) {
    throw bad("nothing to update");
  }
  const changes = {};
  if (input.title !== undefined) changes.title = checkTitle(input.title);
  if (input.startsAt !== undefined) changes.startsAt = checkStartsAt(input.startsAt);
  if (input.capacity !== undefined) changes.capacity = checkCapacity(input.capacity);
  if (input.status !== undefined) changes.status = checkStatus(input.status, ALL_STATUSES);
  changes.location = checkLocation(input.location ?? "");
  return changes;
}

module.exports = { normalizeCreate, normalizeUpdate, ALL_STATUSES };
