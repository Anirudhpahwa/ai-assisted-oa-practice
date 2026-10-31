const Registration = require("../models/Registration");

/** Total seats held by confirmed registrations of an event. */
async function confirmedSeats(eventId) {
  const rows = await Registration.aggregate([
    { $match: { event: eventId, status: "confirmed" } },
    { $group: { _id: null, seats: { $sum: "$seats" } } },
  ]);
  return rows.length ? rows[0].seats : 0;
}

async function seatsLeft(event) {
  return event.capacity - (await confirmedSeats(event._id));
}

/**
 * Confirms waitlisted registrations in the order they registered, for as long as the
 * next one fits in the free seats. Returns the registrations that were promoted.
 */
async function promoteWaitlist(event) {
  let left = await seatsLeft(event);
  const waiting = await Registration.find({ event: event._id, status: "waitlisted" }).sort({
    createdAt: 1,
    _id: 1,
  });
  const promoted = [];
  for (const registration of waiting) {
    if (registration.seats >= left) break;
    registration.status = "confirmed";
    await registration.save();
    left -= registration.seats;
    promoted.push(registration);
  }
  return promoted;
}

module.exports = { confirmedSeats, seatsLeft, promoteWaitlist };
