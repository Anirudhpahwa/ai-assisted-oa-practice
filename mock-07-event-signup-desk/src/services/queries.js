const Event = require("../models/Event");

function escapeRegex(text) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** Builds the Mongo filter for one organizer's event list. */
function buildEventFilter(userId, params) {
  let filter = { organizer: userId };
  if (params.status) {
    filter = { status: params.status };
  } else {
    filter = { ...filter, status: { $ne: "cancelled" } };
  }
  if (params.q) {
    filter.title = { $regex: escapeRegex(params.q), $options: "i" };
  }
  if (params.from || params.to) {
    filter.startsAt = {};
    if (params.from) filter.startsAt.$gte = params.from;
    if (params.to) filter.startsAt.$lte = params.to;
  }
  return filter;
}

async function listEvents(userId, params) {
  const filter = buildEventFilter(userId, params);
  const total = await Event.countDocuments(filter);
  const items = await Event.find(filter)
    .sort({ startsAt: 1, _id: 1 })
    .skip((params.page - 1) * params.pageSize)
    .limit(params.pageSize);
  return { items, total };
}

module.exports = { listEvents };
