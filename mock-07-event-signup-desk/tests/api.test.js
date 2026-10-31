const mongoose = require("mongoose");
const {
  connect,
  reset,
  disconnect,
  as,
  makeEvent,
  makeRegistration,
  Event,
  Registration,
} = require("./helpers");

beforeAll(connect);
afterEach(reset);
afterAll(disconnect);

describe("event sign-up desk", () => {
  test("create event", async () => {
    let res = await as(null).post("/api/events").send({ title: "Launch Night" });
    expect(res.status).toBe(401);
    expect(res.body.error).toBe("X-User-Id header required");

    res = await as("   ").post("/api/events").send({ title: "Launch Night" });
    expect(res.status).toBe(401);

    res = await as("olivia")
      .post("/api/events")
      .send({ title: "  Launch Night  ", startsAt: "2027-02-10T19:00:00Z" });
    expect(res.status).toBe(201);
    expect(res.body.title).toBe("Launch Night");
    expect(res.body.location).toBe("");
    expect(res.body.capacity).toBe(20);
    expect(res.body.status).toBe("draft");
    expect(res.body.organizer).toBe("olivia");
    expect(res.body.startsAt).toBe("2027-02-10T19:00:00.000Z");

    res = await as("olivia")
      .post("/api/events")
      .send({ title: "Garden Party", location: " Hall B ", startsAt: "2027-05-01", capacity: 500, status: "published" });
    expect(res.status).toBe(201);
    expect(res.body.location).toBe("Hall B");
    expect(res.body.capacity).toBe(500);
    expect(res.body.status).toBe("published");

    res = await as("olivia").post("/api/events").send({ title: "ab", startsAt: "2027-02-10" });
    expect(res.status).toBe(400);
    expect(res.body.error).toBe("title must be 3 to 80 characters");

    res = await as("olivia").post("/api/events").send({ title: "Launch Night", startsAt: "tomorrow" });
    expect(res.status).toBe(400);
    expect(res.body.error).toBe("startsAt must be a valid date");

    for (const capacity of [0, 501, 2.5, "10"]) {
      res = await as("olivia").post("/api/events").send({ title: "Launch Night", startsAt: "2027-02-10", capacity });
      expect(res.status).toBe(400);
      expect(res.body.error).toBe("capacity must be an integer from 1 to 500");
    }

    res = await as("olivia")
      .post("/api/events")
      .send({ title: "Launch Night", startsAt: "2027-02-10", status: "cancelled" });
    expect(res.status).toBe(400);
    expect(res.body.error).toBe("status must be draft or published");

    expect(await Event.countDocuments()).toBe(2);
  });

  test("list events", async () => {
    const a = await makeEvent({ title: "Spring Gala", startsAt: new Date("2027-04-10T18:00:00Z") });
    const b = await makeEvent({ title: "Autumn gala", startsAt: new Date("2027-03-05T18:00:00Z"), status: "draft" });
    const c = await makeEvent({ title: "Pottery Class", startsAt: new Date("2027-03-20T10:00:00Z") });
    const d = await makeEvent({ title: "Book Club", startsAt: new Date("2027-03-20T10:00:00Z") });
    const e = await makeEvent({ title: "Old Meetup", startsAt: new Date("2027-01-05T10:00:00Z"), status: "cancelled" });
    await makeEvent({ title: "Noah Draft", organizer: "noah", status: "draft", startsAt: new Date("2027-03-06T10:00:00Z") });
    await makeEvent({ title: "Noah Gala", organizer: "noah", startsAt: new Date("2027-03-07T10:00:00Z") });

    let res = await as("olivia").get("/api/events");
    expect(res.status).toBe(200);
    expect(res.body.items.map((x) => x.id)).toEqual([b, c, d, a].map((x) => String(x._id)));
    expect(res.body.total).toBe(4);
    expect(res.body.page).toBe(1);
    expect(res.body.pageSize).toBe(10);
    expect(res.body.totalPages).toBe(1);

    res = await as("olivia").get("/api/events?status=draft");
    expect(res.body.items.map((x) => x.title)).toEqual(["Autumn gala"]);
    expect(res.body.total).toBe(1);

    res = await as("olivia").get("/api/events?status=cancelled");
    expect(res.body.items.map((x) => x.id)).toEqual([String(e._id)]);

    res = await as("olivia").get("/api/events?q=%20GALA%20");
    expect(res.body.items.map((x) => x.title)).toEqual(["Autumn gala", "Spring Gala"]);

    res = await as("olivia").get("/api/events?from=2027-03-20T10:00:00Z&to=2027-04-10T18:00:00Z");
    expect(res.body.items.map((x) => x.title)).toEqual(["Pottery Class", "Book Club", "Spring Gala"]);

    res = await as("olivia").get("/api/events?status=published&q=gala&pageSize=1");
    expect(res.body.items.map((x) => x.title)).toEqual(["Spring Gala"]);
    expect(res.body.total).toBe(1);

    res = await as("olivia").get("/api/events?pageSize=3&page=2");
    expect(res.body.items.map((x) => x.id)).toEqual([String(a._id)]);
    expect(res.body.page).toBe(2);
    expect(res.body.pageSize).toBe(3);
    expect(res.body.total).toBe(4);
    expect(res.body.totalPages).toBe(2);

    res = await as("olivia").get("/api/events?page=0");
    expect(res.status).toBe(400);
    expect(res.body.error).toBe("page must be a positive integer");

    res = await as("olivia").get("/api/events?pageSize=51");
    expect(res.status).toBe(400);
    expect(res.body.error).toBe("pageSize must be an integer from 1 to 50");

    res = await as("olivia").get("/api/events?from=2027-05-01&to=2027-04-01");
    expect(res.status).toBe(400);
    expect(res.body.error).toBe("from must not be after to");
  });

  test("update event", async () => {
    const event = await makeEvent({ title: "Open Studio", location: "Hall A", capacity: 3 });
    const confirmed = await makeRegistration(event, "kim", { guests: 1 });
    const first = await makeRegistration(event, "lee", { guests: 1, status: "waitlisted" });
    const second = await makeRegistration(event, "mia", { status: "waitlisted" });
    const url = `/api/events/${event._id}`;

    let res = await as("olivia").patch(url).send({ title: "  Studio Night " });
    expect(res.status).toBe(200);
    expect(res.body.title).toBe("Studio Night");
    expect(res.body.location).toBe("Hall A");
    expect(res.body.capacity).toBe(3);
    expect((await Event.findById(event._id)).location).toBe("Hall A");

    res = await as("olivia").patch(url).send({ capacity: 4 });
    expect(res.status).toBe(200);
    expect(res.body.capacity).toBe(4);
    expect((await Event.findById(event._id)).capacity).toBe(4);
    expect((await Registration.findById(confirmed._id)).status).toBe("confirmed");
    expect((await Registration.findById(first._id)).status).toBe("confirmed");
    expect((await Registration.findById(second._id)).status).toBe("waitlisted");

    res = await as("olivia").patch(url).send({ capacity: 3 });
    expect(res.status).toBe(409);
    expect(res.body.error).toBe("capacity is below confirmed seats");

    res = await as("noah").patch(url).send({ title: "Hijacked" });
    expect(res.status).toBe(403);
    expect(res.body.error).toBe("only the organizer can do that");

    res = await as("olivia").patch(`/api/events/${new mongoose.Types.ObjectId()}`).send({ title: "Whatever" });
    expect(res.status).toBe(404);
    expect(res.body.error).toBe("event not found");

    res = await as("olivia").patch(url).send({});
    expect(res.status).toBe(400);
    expect(res.body.error).toBe("nothing to update");

    res = await as("olivia").patch(url).send({ capacity: 500, title: "ab" });
    expect(res.status).toBe(400);

    res = await as("olivia").patch(url).send({ capacity: 500 });
    expect(res.status).toBe(200);
    expect((await Registration.findById(second._id)).status).toBe("confirmed");

    res = await as("olivia").patch(url).send({ status: "draft" });
    expect(res.status).toBe(409);
    expect(res.body.error).toBe("invalid status change");

    res = await as("olivia").patch(url).send({ status: "cancelled" });
    expect(res.status).toBe(200);
    expect(res.body.status).toBe("cancelled");

    res = await as("olivia").patch(url).send({ title: "Too late" });
    expect(res.status).toBe(409);
    expect(res.body.error).toBe("event is cancelled");
  });

  test("register for event", async () => {
    const event = await makeEvent({ capacity: 3 });
    const url = `/api/events/${event._id}/registrations`;

    let res = await as("noah").post(url).send({ guests: 1 });
    expect(res.status).toBe(201);
    expect(res.body.status).toBe("confirmed");
    expect(res.body.seats).toBe(2);
    expect(res.body.guests).toBe(1);
    expect(res.body.userId).toBe("noah");
    expect(res.body.eventId).toBe(String(event._id));

    res = await as("mia").post(url).send({ guests: 1 });
    expect(res.status).toBe(201);
    expect(res.body.status).toBe("waitlisted");
    expect(res.body.seats).toBe(2);

    res = await as("lee").post(url).send({});
    expect(res.status).toBe(201);
    expect(res.body.status).toBe("confirmed");
    expect(res.body.seats).toBe(1);

    res = await as("mia").post(url).send({});
    expect(res.status).toBe(409);
    expect(res.body.error).toBe("already registered");

    for (const guests of [4, -1, "1", 1.5]) {
      res = await as("zed").post(url).send({ guests });
      expect(res.status).toBe(400);
      expect(res.body.error).toBe("guests must be an integer from 0 to 3");
    }

    await Registration.updateOne({ event: event._id, userId: "noah" }, { status: "cancelled" });
    res = await as("noah").post(url).send({});
    expect(res.status).toBe(201);
    expect(res.body.status).toBe("confirmed");
    expect(await Registration.countDocuments({ event: event._id, userId: "noah" })).toBe(2);

    const draft = await makeEvent({ status: "draft" });
    res = await as("noah").post(`/api/events/${draft._id}/registrations`).send({});
    expect(res.status).toBe(409);
    expect(res.body.error).toBe("event is not open for registration");

    res = await as("noah").post(`/api/events/${new mongoose.Types.ObjectId()}/registrations`).send({});
    expect(res.status).toBe(404);
    expect(res.body.error).toBe("event not found");
  });

  test("cancel registration", async () => {
    const event = await makeEvent({ capacity: 3 });
    const noah = await makeRegistration(event, "noah", { guests: 1 });
    const lee = await makeRegistration(event, "lee");
    const mia = await makeRegistration(event, "mia", { guests: 1, status: "waitlisted" });
    const zed = await makeRegistration(event, "zed", { status: "waitlisted" });
    const base = `/api/events/${event._id}/registrations`;

    let res = await as("noah").delete(`${base}/${noah._id}`);
    expect(res.status).toBe(200);
    expect(res.body.registration.status).toBe("cancelled");
    expect(res.body.registration.id).toBe(String(noah._id));
    expect(res.body.promoted).toEqual([String(mia._id)]);
    expect((await Registration.findById(mia._id)).status).toBe("confirmed");
    expect((await Registration.findById(zed._id)).status).toBe("waitlisted");

    res = await as("noah").delete(`${base}/${noah._id}`);
    expect(res.status).toBe(409);
    expect(res.body.error).toBe("registration already cancelled");

    res = await as("zed").delete(`${base}/${lee._id}`);
    expect(res.status).toBe(403);
    expect(res.body.error).toBe("not allowed to cancel this registration");
    expect((await Registration.findById(lee._id)).status).toBe("confirmed");

    const other = await makeEvent({ title: "Other Event" });
    const stray = await makeRegistration(other, "noah");
    res = await as("noah").delete(`${base}/${stray._id}`);
    expect(res.status).toBe(404);
    expect(res.body.error).toBe("registration not found");
    expect((await Registration.findById(stray._id)).status).toBe("confirmed");

    res = await as("noah").delete(`${base}/${new mongoose.Types.ObjectId()}`);
    expect(res.status).toBe(404);

    res = await as("olivia").delete(`${base}/${lee._id}`);
    expect(res.status).toBe(200);
    expect(res.body.promoted).toEqual([String(zed._id)]);
    expect((await Registration.findById(zed._id)).status).toBe("confirmed");

    res = await as("zed").delete(`${base}/${zed._id}`);
    expect(res.status).toBe(200);
    expect(res.body.promoted).toEqual([]);
  });

  test("event summary", async () => {
    const event = await makeEvent({ capacity: 10 });
    await makeRegistration(event, "kim", { guests: 3 });
    await makeRegistration(event, "lee", { guests: 1 });
    await makeRegistration(event, "mia", { guests: 3, status: "waitlisted" });
    await makeRegistration(event, "noah", { status: "cancelled" });
    await makeRegistration(event, "zed", { guests: 1, status: "cancelled" });

    let res = await as("olivia").get(`/api/events/${event._id}/summary`);
    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      eventId: String(event._id),
      capacity: 10,
      confirmedCount: 2,
      confirmedSeats: 6,
      waitlistedCount: 1,
      cancelledCount: 2,
      seatsLeft: 4,
      fillRate: 60,
    });

    const third = await makeEvent({ capacity: 3 });
    await makeRegistration(third, "kim");
    res = await as("olivia").get(`/api/events/${third._id}/summary`);
    expect(res.body.fillRate).toBe(33);
    expect(res.body.seatsLeft).toBe(2);

    const eighth = await makeEvent({ capacity: 8 });
    await makeRegistration(eighth, "kim", { guests: 3 });
    await makeRegistration(eighth, "lee");
    res = await as("olivia").get(`/api/events/${eighth._id}/summary`);
    expect(res.body.fillRate).toBe(63);

    const empty = await makeEvent({ capacity: 5 });
    res = await as("olivia").get(`/api/events/${empty._id}/summary`);
    expect(res.body.confirmedCount).toBe(0);
    expect(res.body.fillRate).toBe(0);
    expect(res.body.seatsLeft).toBe(5);

    res = await as("noah").get(`/api/events/${event._id}/summary`);
    expect(res.status).toBe(403);
    expect(res.body.error).toBe("only the organizer can do that");

    res = await as("olivia").get(`/api/events/${new mongoose.Types.ObjectId()}/summary`);
    expect(res.status).toBe(404);
  });
});
