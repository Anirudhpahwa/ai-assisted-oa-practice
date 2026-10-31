const Event = require("../models/Event");
const { HttpError, isObjectId } = require("../errors");

/** Loads the event named by :id onto req.event. */
async function loadEvent(req, res, next) {
  const event = isObjectId(req.params.id) ? await Event.findById(req.params.id) : null;
  if (!event) {
    throw new HttpError(404, "event not found");
  }
  req.event = event;
  next();
}

function requireOrganizer(req, res, next) {
  if (req.event.organizer !== req.userId) {
    throw new HttpError(403, "only the organizer can do that");
  }
  next();
}

module.exports = { loadEvent, requireOrganizer };
