const mongoose = require("mongoose");
const request = require("supertest");
const { MongoMemoryServer } = require("mongodb-memory-server");
const app = require("../src/app");
const Event = require("../src/models/Event");
const Registration = require("../src/models/Registration");

let mongod;

async function connect() {
  mongod = await MongoMemoryServer.create();
  await mongoose.connect(mongod.getUri());
}

async function reset() {
  await Promise.all(Object.values(mongoose.connection.collections).map((c) => c.deleteMany({})));
}

async function disconnect() {
  await mongoose.disconnect();
  await mongod.stop();
}

/** Returns get/post/patch/delete helpers that send the given user in X-User-Id. */
function as(user) {
  const send = (method) => (path) => {
    const req = request(app)[method](path);
    return user === null ? req : req.set("X-User-Id", user);
  };
  return { get: send("get"), post: send("post"), patch: send("patch"), delete: send("delete") };
}

function makeEvent(overrides = {}) {
  return Event.create({
    title: "Open Studio",
    location: "Room 1",
    startsAt: new Date("2027-03-01T18:00:00Z"),
    capacity: 10,
    status: "published",
    organizer: "olivia",
    ...overrides,
  });
}

function makeRegistration(event, userId, { guests = 0, status = "confirmed" } = {}) {
  return Registration.create({ event: event._id, userId, guests, seats: 1 + guests, status });
}

module.exports = { connect, reset, disconnect, as, makeEvent, makeRegistration, Event, Registration };
