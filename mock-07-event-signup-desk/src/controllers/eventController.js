const Event = require("../models/Event");
const { HttpError } = require("../errors");
const { normalizeCreate, normalizeUpdate } = require("../validators/eventValidator");
const { parseListParams } = require("../validators/listParams");
const { listEvents } = require("../services/queries");
const { confirmedSeats, promoteWaitlist } = require("../services/capacity");
const { serializeEvent } = require("../serializers");

const STATUS_CHANGES = {
  draft: ["published", "cancelled"],
  published: ["cancelled"],
};

async function create(req, res) {
  const data = normalizeCreate(req.body);
  const event = await Event.create({ ...data, organizer: req.userId });
  res.status(201).json(serializeEvent(event));
}

async function list(req, res) {
  const params = parseListParams(req.query);
  const { items, total } = await listEvents(req.userId, params);
  res.json({
    items: items.map(serializeEvent),
    page: params.page,
    pageSize: params.pageSize,
    total,
    totalPages: Math.ceil(total / params.pageSize),
  });
}

function show(req, res) {
  res.json(serializeEvent(req.event));
}

async function update(req, res) {
  const changes = normalizeUpdate(req.body);
  const event = req.event;
  if (event.status === "cancelled") {
    throw new HttpError(409, "event is cancelled");
  }
  if (changes.status && changes.status !== event.status) {
    const allowed = STATUS_CHANGES[event.status] || [];
    if (!allowed.includes(changes.status)) {
      throw new HttpError(409, "invalid status change");
    }
  }
  if (changes.capacity !== undefined && changes.capacity < (await confirmedSeats(event._id))) {
    throw new HttpError(409, "capacity is below confirmed seats");
  }
  event.set(changes);
  await event.save();
  if (changes.capacity !== undefined && changes.capacity > event.capacity) {
    await promoteWaitlist(event);
  }
  res.json(serializeEvent(event));
}

module.exports = { create, list, show, update };
