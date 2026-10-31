function serializeEvent(event) {
  return {
    id: String(event._id),
    title: event.title,
    location: event.location,
    startsAt: event.startsAt.toISOString(),
    capacity: event.capacity,
    status: event.status,
    organizer: event.organizer,
    createdAt: event.createdAt.toISOString(),
  };
}

function serializeRegistration(registration) {
  return {
    id: String(registration._id),
    eventId: String(registration.event),
    userId: registration.userId,
    guests: registration.guests,
    seats: registration.seats,
    status: registration.status,
    createdAt: registration.createdAt.toISOString(),
  };
}

module.exports = { serializeEvent, serializeRegistration };
