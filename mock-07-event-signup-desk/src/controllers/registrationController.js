const Registration = require("../models/Registration");
const { HttpError, isObjectId } = require("../errors");
const { readGuests } = require("../validators/registrationValidator");
const { seatsLeft, promoteWaitlist } = require("../services/capacity");
const { serializeRegistration } = require("../serializers");

async function create(req, res) {
  const event = req.event;
  const guests = readGuests(req.body);
  if (event.status !== "published") {
    throw new HttpError(409, "event is not open for registration");
  }
  const existing = await Registration.findOne({
    event: event._id,
    userId: req.userId,
  });
  if (existing) {
    throw new HttpError(409, "already registered");
  }
  const seats = 1 + guests;
  const status = seats <= (await seatsLeft(event)) ? "confirmed" : "waitlisted";
  const registration = await Registration.create({
    event: event._id,
    userId: req.userId,
    guests,
    seats,
    status,
  });
  res.status(201).json(serializeRegistration(registration));
}

async function cancel(req, res) {
  const event = req.event;
  const registration = isObjectId(req.params.regId)
    ? await Registration.findById(req.params.regId)
    : null;
  if (!registration) {
    throw new HttpError(404, "registration not found");
  }
  if (registration.userId !== req.userId && event.organizer !== req.userId) {
    throw new HttpError(403, "not allowed to cancel this registration");
  }
  if (registration.status === "cancelled") {
    throw new HttpError(409, "registration already cancelled");
  }
  const wasConfirmed = registration.status === "confirmed";
  registration.status = "cancelled";
  await registration.save();
  const promoted = wasConfirmed ? await promoteWaitlist(event) : [];
  res.json({
    registration: serializeRegistration(registration),
    promoted: promoted.map((item) => String(item._id)),
  });
}

module.exports = { create, cancel };
