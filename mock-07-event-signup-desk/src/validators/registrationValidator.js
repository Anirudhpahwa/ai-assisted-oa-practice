const { HttpError } = require("../errors");

const MAX_GUESTS = 3;

/** Returns the number of extra guests for a registration body (0 when absent). */
function readGuests(body) {
  const guests = body && typeof body === "object" ? body.guests : undefined;
  if (guests === undefined) return 0;
  if (!Number.isInteger(guests) || guests < 0 || guests > MAX_GUESTS) {
    throw new HttpError(400, "guests must be an integer from 0 to 3");
  }
  return guests;
}

module.exports = { readGuests };
