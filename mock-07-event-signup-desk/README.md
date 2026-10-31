# Event Sign-up Desk (React + Node.js)

An internal tool for a community center. Organizers publish events with a limited number of seats, attendees sign up (optionally bringing guests), and people who do not fit go on a waitlist that fills up as seats free up.

The React app lives in `frontend/`, the Express + Mongoose API in `src/`. The backend is what the tests cover.

## Who is acting

Every request must carry the `X-User-Id` header with the acting person's id. The value is trimmed. If the header is missing or empty after trimming, the response is `401` with `{ "error": "X-User-Id header required" }`.

All errors are JSON: `{ "error": "<message>" }`. Where a message is given below it is exact. An `:id` or `:regId` that is not a real id counts as not found.

## Data

**Event**

| Field | Rules |
|---|---|
| `title` | text, trimmed, 3 to 80 characters |
| `location` | text, trimmed, at most 120 characters, default `""` |
| `startsAt` | a date |
| `capacity` | whole number from 1 to 500 (both ends allowed; a number given as text is not accepted), default `20` |
| `status` | `draft`, `published` or `cancelled`, default `draft` |
| `organizer` | the `X-User-Id` of whoever created it |

**Registration**

| Field | Rules |
|---|---|
| `userId` | the `X-User-Id` of the attendee |
| `guests` | whole number from 0 to 3, default `0` |
| `seats` | `1 + guests` |
| `status` | `confirmed`, `waitlisted` or `cancelled` |

**Waitlist promotion.** Whenever seats may have been freed, waitlisted registrations of the event are looked at in the order they registered. Each one whose `seats` fit in the free seats is changed to `confirmed`, and the free seats shrink accordingly. The first one that does not fit stops the process; nobody behind it is promoted, even if they would fit. Free seats are the event's `capacity` minus the `seats` of its `confirmed` registrations.

## Endpoints

All paths start with `/api/events`.

### POST `/`

Creates an event. Body fields: `title` (required), `startsAt` (required), `location`, `capacity`, `status`. On create `status` may only be `draft` or `published`.

- `400` when a field breaks its rule. Checked in this order, first failure reported:
  - `title must be 3 to 80 characters`
  - `location must be at most 120 characters`
  - `startsAt must be a valid date` (it must be a string that parses as a date)
  - `capacity must be an integer from 1 to 500`
  - `status must be draft or published`
- `201` with the event. The organizer is the acting user.

Event response shape:

```json
{
  "id": "65f1c0a2b7d4e9a1c3f5b801",
  "title": "Launch Night",
  "location": "Hall B",
  "startsAt": "2027-02-10T19:00:00.000Z",
  "capacity": 20,
  "status": "draft",
  "organizer": "olivia",
  "createdAt": "2027-01-02T09:30:00.000Z"
}
```

### GET `/`

Lists the events organized by the acting user. Other people's events never appear. Query parameters, all optional:

- `status`: `draft`, `published` or `cancelled`; any other value is `400` with `status must be draft, published or cancelled`. When it is not given, cancelled events are left out. When it is given, only events with that status are returned.
- `q`: text, trimmed; keeps events whose `title` contains it, ignoring upper/lower case. Empty means no filtering.
- `from`, `to`: dates; keep events whose `startsAt` is on or after `from` and on or before `to` (both ends included). A value that is not a valid date is `400` with `from must be a valid date` or `to must be a valid date`. If both are given and `from` is after `to`: `400` with `from must not be after to`.
- `page`: whole number of 1 or more, default `1`; otherwise `400` with `page must be a positive integer`.
- `pageSize`: whole number from 1 to 50, default `10`; otherwise `400` with `pageSize must be an integer from 1 to 50`.

All filters apply together. Events are ordered by `startsAt` (earliest first); events with the same `startsAt` keep the order they were created in. `total` counts every matching event, not only those on the page, and `totalPages` is `total` divided by `pageSize`, rounded up (0 when there are no matches).

```json
{
  "items": [ { "id": "65f1c0a2b7d4e9a1c3f5b801", "title": "Launch Night", "...": "..." } ],
  "page": 1,
  "pageSize": 10,
  "total": 1,
  "totalPages": 1
}
```

### GET `/:id`

Returns the event (any user may read it). `404` with `event not found` if there is no such event.

### PATCH `/:id`

Changes an event. Only the organizer may do this.

- `404` `event not found`, then `403` `only the organizer can do that` for anyone else.
- `400` `nothing to update` when the body has none of `title`, `location`, `startsAt`, `capacity`, `status`.
- The fields that are present follow the same rules and `400` messages as create, except that `status` may be any of `draft`, `published`, `cancelled` (message `status must be draft, published or cancelled`). Fields that are not in the body keep their current values.
- `409` `event is cancelled` when the event is already cancelled (no field can be changed any more).
- `409` `invalid status change` unless the change is `draft` to `published`, `draft` to `cancelled`, `published` to `cancelled`, or the same status as now.
- `409` `capacity is below confirmed seats` when the new `capacity` is lower than the seats held by the event's confirmed registrations.
- When `capacity` is raised, waitlist promotion runs after the change is saved.
- `200` with the updated event.

Checks run in this order: 404, 403, 400, 409.

### POST `/:id/registrations`

The acting user signs up for the event. Body: `guests` (optional).

- `404` `event not found`.
- `400` `guests must be an integer from 0 to 3` when `guests` is present but is not a whole number from 0 to 3 (a number given as text is not accepted).
- `409` `event is not open for registration` unless the event is `published`.
- `409` `already registered` when the user already has a `confirmed` or `waitlisted` registration for this event. A `cancelled` one does not count, so the user may sign up again; that creates a new registration.
- Otherwise a registration is created with `seats = 1 + guests`. It is `confirmed` if `seats` fit in the free seats, and `waitlisted` if not.
- `201` with the registration, in both cases.

Checks run in this order: 404, 400, 409.

```json
{
  "id": "65f1c0a2b7d4e9a1c3f5b8a2",
  "eventId": "65f1c0a2b7d4e9a1c3f5b801",
  "userId": "noah",
  "guests": 1,
  "seats": 2,
  "status": "confirmed",
  "createdAt": "2027-01-03T10:00:00.000Z"
}
```

### DELETE `/:id/registrations/:regId`

Cancels a registration (it stays on record with status `cancelled`).

- `404` `event not found`.
- `404` `registration not found` when no registration with that id belongs to this event.
- `403` `not allowed to cancel this registration` unless the acting user is the person who registered or the event's organizer.
- `409` `registration already cancelled`.
- Otherwise the status becomes `cancelled`. If the registration was `confirmed`, waitlist promotion runs afterwards; cancelling a `waitlisted` one frees nothing, so nobody is promoted.
- `200` with the cancelled registration and the ids of the registrations that were promoted, in the order they were promoted (an empty list when none).

```json
{
  "registration": { "id": "65f1c0a2b7d4e9a1c3f5b8a2", "status": "cancelled", "...": "..." },
  "promoted": ["65f1c0a2b7d4e9a1c3f5b8b7"]
}
```

### GET `/:id/summary`

Seat figures for one event. Only the organizer may read it (`404` `event not found`, then `403` `only the organizer can do that`).

```json
{
  "eventId": "65f1c0a2b7d4e9a1c3f5b801",
  "capacity": 10,
  "confirmedCount": 2,
  "confirmedSeats": 6,
  "waitlistedCount": 1,
  "cancelledCount": 2,
  "seatsLeft": 4,
  "fillRate": 60
}
```

- `confirmedCount`, `waitlistedCount`, `cancelledCount`: how many registrations have that status.
- `confirmedSeats`: the sum of `seats` over confirmed registrations.
- `seatsLeft`: `capacity` minus `confirmedSeats`.
- `fillRate`: `confirmedSeats` as a percentage of `capacity`, rounded to the nearest whole number (halves round up).

## Running the tests

From the project root:

```
npm install
npm test
```

The tests start their own in-memory MongoDB. The first run downloads a MongoDB binary (about 100 MB), so allow a little time and an internet connection for it.
