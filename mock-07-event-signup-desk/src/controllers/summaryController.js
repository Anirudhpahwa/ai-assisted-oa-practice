const Registration = require("../models/Registration");

async function show(req, res) {
  const event = req.event;
  const groups = await Registration.aggregate([
    { $match: { event: event._id } },
    { $group: { _id: "$status", count: { $sum: 1 }, seats: { $sum: "$seats" } } },
  ]);
  const byStatus = (status) => groups.find((group) => group._id === status) || { count: 0, seats: 0 };
  const confirmed = byStatus("confirmed");
  res.json({
    eventId: String(event._id),
    capacity: event.capacity,
    confirmedCount: confirmed.count,
    confirmedSeats: confirmed.seats,
    waitlistedCount: byStatus("waitlisted").count,
    cancelledCount: byStatus("cancelled").count,
    seatsLeft: event.capacity - confirmed.seats,
    fillRate: Math.round((confirmed.count / event.capacity) * 100),
  });
}

module.exports = { show };
