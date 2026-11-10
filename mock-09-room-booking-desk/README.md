# Room Booking Desk (Spring Boot)

An internal tool for an office with meeting rooms. People book a room for a time slot, retry safely if their request is repeated, cancel with a fee that depends on how late they cancel, and a manager reads availability and monthly figures for each room.

The code lives in `src/main/java/com/example/roombooking`, the tests in `src/test/java`. The tests call the HTTP API described below, so the whole app is covered by them. Rooms are set up elsewhere; this API only reads them.

## Who is acting

Every request must carry two headers:

- `X-User`: the acting person's name. The value is trimmed. If it is missing or empty after trimming, the response is `401` with `{ "error": "X-User header required" }`.
- `X-Role`: `USER` or `MANAGER`, any upper/lower case, trimmed. When the header is missing or empty the role is `USER`. Any other value is `400` with `role must be USER or MANAGER`. The user header is checked first.

All errors are JSON: `{ "error": "<message>" }`. Where a message is given below it is exact. An `{id}` in a path that is not a number is `404` with `not found`.

## Data

**Room**: `name`, `capacity` (whole number of people), `hourlyRateCents`, `active`. An inactive room, or one that does not exist, is `404` with `room not found` wherever a room is used.

**Booking**

| Field | Rules |
|---|---|
| `roomId` | the booked room |
| `bookedBy` | the `X-User` of whoever made it |
| `title` | text, trimmed, 3 to 80 characters |
| `startsAt`, `endsAt` | date-times in ISO 8601 with a `Z` or an offset such as `+01:00`; they are stored and returned in UTC, for example `2027-03-02T09:00:00Z` |
| `attendees` | whole number from 1 up to the room's capacity |
| `status` | `CONFIRMED` or `CANCELLED` |
| `totalCents` | the price of the booking, see below |
| `feeCents` | the cancellation fee; `0` until cancelled |
| `cancelledAt` | when it was cancelled, otherwise `null` |

Booking response shape (used by every endpoint that returns a booking):

```json
{
  "id": 7,
  "roomId": 1,
  "bookedBy": "ana",
  "title": "Sprint planning",
  "startsAt": "2027-03-02T09:00:00Z",
  "endsAt": "2027-03-02T10:30:00Z",
  "attendees": 5,
  "status": "CONFIRMED",
  "totalCents": 7500,
  "feeCents": 0,
  "createdAt": "2027-03-01T12:00:00Z",
  "cancelledAt": null
}
```

**Money.** All amounts are whole cents. Whenever a calculation does not come out in whole cents it is rounded to the nearest cent, with halves rounded up.

## Endpoints

### POST `/api/bookings`

Books a room. Body fields: `roomId`, `title`, `startsAt`, `endsAt`, `attendees`, all required. Optional header `Idempotency-Key`.

Checks run in this order:

1. `401` / `400` for the headers, as above.
2. **Idempotency key.** The key is trimmed; an empty key counts as no key. A key longer than 64 characters is `400` with `Idempotency-Key must be at most 64 characters`. When there is a key and the acting user already made a booking with the same key, that earlier booking is returned unchanged with status `200`, and nothing else in this list is checked or changed, whatever the body says. Keys belong to the user who sent them: two users may use the same key for different bookings.
3. `400` for a body field that breaks its rule, in this order, first failure reported:
   - `title must be 3 to 80 characters`
   - `roomId is required`
   - `startsAt must be a valid date-time`
   - `endsAt must be a valid date-time`
   - `endsAt must be after startsAt`
   - `duration must be 30 minutes to 8 hours in 30-minute steps` (the length must be a whole number of half hours, from 30 minutes to 8 hours, both included)
   - `attendees must be a whole number of 1 or more`
4. `404` `room not found`.
5. `400` `attendees must not exceed the room capacity`.
6. `409` `room is already booked for that time` when a `CONFIRMED` booking of the same room overlaps the new one. Two bookings overlap when each starts before the other ends; a booking that ends exactly when another starts does not overlap it. Cancelled bookings never conflict.
7. Otherwise the booking is created as `CONFIRMED` with `feeCents` 0 and `201`. `totalCents` is the room's `hourlyRateCents` for the booked time: `hourlyRateCents` times the number of minutes, divided by 60, rounded as described under Money.

### GET `/api/bookings`

Lists bookings (every user sees every booking). All query parameters are optional and apply together:

- `roomId`: a whole number; anything else is `400` with `roomId must be a whole number`.
- `bookedBy`: keeps bookings made by exactly this user (after trimming).
- `status`: `CONFIRMED` or `CANCELLED`, any upper/lower case; anything else is `400` with `status must be CONFIRMED or CANCELLED`. Without it both statuses are listed.
- `from`, `to`: date-times as above. A booking is kept when its `startsAt` is on or after `from` and before `to` (`to` itself is not included). A value that is not a date-time is `400` with `from must be a valid date-time` or `to must be a valid date-time`. When both are given, `from` must be earlier than `to`; otherwise `400` with `from must be before to`.
- `page`: zero-based page number, default `0`; a negative or non-numeric value is `400` with `page must be zero or a positive integer`.
- `size`: page size from 1 to 100, default `20`; otherwise `400` with `size must be an integer from 1 to 100`.

Bookings are ordered by `startsAt`, earliest first; bookings with the same `startsAt` are ordered by `id`, lowest first. `totalElements` counts every matching booking, not only those on the page, and `totalPages` is `totalElements` divided by `size`, rounded up (0 when nothing matches). A page past the end has an empty `items` list.

```json
{
  "items": [ { "id": 7, "title": "Sprint planning", "...": "..." } ],
  "page": 0,
  "size": 20,
  "totalElements": 1,
  "totalPages": 1
}
```

### GET `/api/bookings/{id}`

Returns the booking, or `404` `booking not found`.

### POST `/api/bookings/{id}/cancel`

Cancels a booking. No body.

Checks run in this order:

1. `404` `booking not found`.
2. `403` `only the booker or a manager can cancel` unless the acting user is `bookedBy` (exact match) or the role is `MANAGER`.
3. `409` `booking already cancelled`.
4. `409` `booking has already started` when the current time is at or after `startsAt`.

Then the booking becomes `CANCELLED`, `cancelledAt` is the current time and `feeCents` is a share of `totalCents`, depending on how long is left until `startsAt`:

| Time left until `startsAt` | Fee |
|---|---|
| 24 hours or more | 0% |
| 2 hours or more, but less than 24 hours | 50% |
| less than 2 hours | 100% |

`200` with the booking.

### GET `/api/rooms/{id}/availability?date=YYYY-MM-DD`

The free time of a room on one UTC day. The room can be booked from 08:00 to 20:00 UTC. The response lists the free windows inside that period, in time order; each window runs from the end of one `CONFIRMED` booking to the start of the next, or to opening and closing time. A booking that begins before 08:00 or ends after 20:00 blocks only the part inside the period. Windows with no length are not listed. Cancelled bookings and other rooms' bookings are ignored.

`404` `room not found` is checked first, then `400` `date must be a valid YYYY-MM-DD date` when `date` is missing or not a real date.

```json
{
  "roomId": 1,
  "date": "2027-03-02",
  "free": [
    { "startsAt": "2027-03-02T09:00:00Z", "endsAt": "2027-03-02T11:00:00Z" }
  ]
}
```

### GET `/api/rooms/{id}/report?month=YYYY-MM`

Usage and income of a room for the bookings whose `startsAt` falls in one UTC calendar month (from the first day at 00:00 up to, but not including, the first day of the next month at 00:00). `404` `room not found` is checked first, then `400` `month must be a valid YYYY-MM month` when `month` is missing or not a real month.

```json
{
  "roomId": 1,
  "month": "2027-03",
  "confirmedCount": 3,
  "cancelledCount": 2,
  "bookedMinutes": 240,
  "revenueCents": 22500
}
```

- `confirmedCount`, `cancelledCount`: how many bookings of the month have that status.
- `bookedMinutes`: the minutes from `startsAt` to `endsAt`, added up over the confirmed bookings only.
- `revenueCents`: the `totalCents` of the confirmed bookings plus the `feeCents` of the cancelled ones.

## Running the tests

You need JDK 17 or newer. From the project root:

```
mvnw.cmd test        (Windows)
sh mvnw test         (macOS / Linux)
```

The first run downloads Maven and the project's libraries, so allow a minute and an internet connection. Later runs are faster. There is nothing else to install or start. The tests use a fixed clock, so the result does not depend on the date you run them.
