# Work Order Desk (Spring Boot)

An internal tool for a building maintenance team. People report jobs as work orders, a manager assigns them, technicians move them through a simple workflow and record the parts they use, and every change is kept in a history.

The code lives in `src/main/java/com/example/workorders`, the tests in `src/test/java`. The tests call the HTTP API described below, so the whole app is covered by them.

## Who is acting

Every request must carry two headers:

- `X-User`: the acting person's name. The value is trimmed. If it is missing or empty after trimming, the response is `401` with `{ "error": "X-User header required" }`.
- `X-Role`: `TECHNICIAN` or `MANAGER`, any upper/lower case, trimmed. When the header is missing or empty the role is `TECHNICIAN`. Any other value is `400` with `role must be TECHNICIAN or MANAGER`. The user header is checked first.

All errors are JSON: `{ "error": "<message>" }`. Where a message is given below it is exact. An `{id}` that does not belong to a work order, or is not a number, is `404` with `work order not found`.

## Data

**Work order**

| Field | Rules |
|---|---|
| `title` | text, trimmed, 3 to 100 characters |
| `description` | text, trimmed, at most 500 characters, default `""` |
| `location` | text, trimmed, at most 100 characters, default `""` |
| `priority` | `URGENT`, `HIGH`, `MEDIUM` or `LOW` (any upper/lower case is accepted), default `MEDIUM` |
| `status` | `OPEN`, `IN_PROGRESS`, `ON_HOLD`, `DONE` or `CANCELLED`; a new order is `OPEN` |
| `assignee` | text, trimmed, 1 to 50 characters; `null` until someone is assigned |
| `createdBy` | the `X-User` of whoever created it |

**Part** (used on a work order): `name` (trimmed, 1 to 60 characters), `quantity` (whole number from 1 to 100), `unitCostCents` (whole number from 0 to 1000000). Both numbers must be given.

**History entry**: `action`, `detail`, `actor` (the `X-User` that made the change) and `at`.

Work order response shape (used by every endpoint that returns an order):

```json
{
  "id": 12,
  "title": "Fix pump",
  "description": "Leaks at base",
  "location": "Basement",
  "priority": "MEDIUM",
  "status": "OPEN",
  "assignee": null,
  "createdBy": "dana",
  "createdAt": "2027-01-02T09:30:00Z",
  "updatedAt": "2027-01-02T09:30:00Z"
}
```

## Endpoints

All paths start with `/api/orders`.

### POST ``

Creates a work order. Body fields: `title` (required), `description`, `location`, `priority`.

- `400` when a field breaks its rule. Checked in this order, first failure reported:
  - `title must be 3 to 100 characters`
  - `description must be at most 500 characters`
  - `location must be at most 100 characters`
  - `priority must be URGENT, HIGH, MEDIUM or LOW`
- `201` with the work order. A history entry is recorded with `action` `CREATED` and `detail` `created`.

### GET ``

Lists work orders (every user sees every order). All query parameters are optional and apply together:

- `status`: a comma-separated list such as `open,on_hold` (any upper/lower case). An unknown name is `400` with `status must be a comma-separated list of OPEN, IN_PROGRESS, ON_HOLD, DONE, CANCELLED`. When `status` is not given, cancelled orders are left out. When it is given, exactly the listed statuses are returned, so `CANCELLED` is only included if it is in the list.
- `priority`: one priority; anything else is `400` with `priority must be URGENT, HIGH, MEDIUM or LOW`.
- `assignee`: keeps orders whose assignee is exactly this name (after trimming).
- `q`: text, trimmed; keeps orders whose `title` or `description` contains it, ignoring upper/lower case.
- `sort`: `newest` (default) or `priority`; anything else is `400` with `sort must be newest or priority`. `newest` puts the most recently created first (newer `createdAt` first; the higher `id` first when they are equal). `priority` goes from `URGENT` down to `LOW`; orders with the same priority are ordered oldest first (older `createdAt` first; the lower `id` first when they are equal).
- `page`: whole number of 1 or more, default `1`; otherwise `400` with `page must be a positive integer`.
- `size`: whole number from 1 to 50, default `10`; otherwise `400` with `size must be an integer from 1 to 50`.

`total` counts every matching order, not only those on the page, and `totalPages` is `total` divided by `size`, rounded up (0 when nothing matches). A page past the end has an empty `items` list.

```json
{
  "items": [ { "id": 12, "title": "Fix pump", "...": "..." } ],
  "page": 1,
  "size": 10,
  "total": 1,
  "totalPages": 1
}
```

### GET `/{id}`

Returns the work order.

### PATCH `/{id}`

Changes a work order. Body fields: `title`, `description`, `location`, `priority`, `assignee`. A field that is missing or `null` is left as it is; the others follow the same rules and `400` messages as create, and `assignee` must be 1 to 50 characters after trimming (`assignee must be 1 to 50 characters`). Priority names are stored in upper case.

Checks run in this order:

1. `404` `work order not found`.
2. `400` `nothing to update` when none of the five fields is given, then `400` for a field that breaks its rule (title, description, location, priority, assignee, in that order).
3. `403` `only a manager can change priority or assignee` when the body contains `priority` or `assignee` and the acting role is not `MANAGER`.
4. `409` `work order is closed` when the order is `DONE` or `CANCELLED`.

Then the changes are applied. For every field whose new value (after trimming) differs from the current one, one history entry is recorded with `action` `UPDATED` and `detail` `<field>: <old> -> <new>`, for example `location: Basement -> Boiler room`. Entries are recorded in the order title, description, location, priority, assignee. An assignee that was `null` shows as `none` in `<old>`. A field whose value does not change records nothing. `200` with the work order.

### POST `/{id}/transition`

Moves the order to another status. Body: `status` (required, any upper/lower case), `note` (optional, trimmed, at most 200 characters).

Checks run in this order:

1. `404` `work order not found`.
2. `400` `status must be one of OPEN, IN_PROGRESS, ON_HOLD, DONE, CANCELLED`, then `400` `note must be at most 200 characters`.
3. `403` `only a manager can cancel` when the new status is `CANCELLED` and the acting role is not `MANAGER`.
4. `409` `invalid transition` unless the move is allowed:

   | From | To |
   |---|---|
   | `OPEN` | `IN_PROGRESS`, `CANCELLED` |
   | `IN_PROGRESS` | `ON_HOLD`, `DONE`, `CANCELLED` |
   | `ON_HOLD` | `IN_PROGRESS`, `CANCELLED` |
   | `DONE`, `CANCELLED` | nothing |

5. `409` `assignee required` when the new status is `IN_PROGRESS` and the order has no assignee.

Then the status changes and one history entry is recorded with `action` `STATUS_CHANGED` and `detail` `<old status> -> <new status>`, followed by ` (<note>)` when a non-empty note was given, for example `OPEN -> IN_PROGRESS (start now)`. `200` with the work order.

### POST `/{id}/parts`

Records a part used on the order. Body: `name`, `quantity`, `unitCostCents`.

Checks run in this order:

1. `404` `work order not found`.
2. `400` for a field that breaks its rule, in the order name, quantity, unit cost: `name must be 1 to 60 characters`, `quantity must be an integer from 1 to 100`, `unitCostCents must be an integer from 0 to 1000000`.
3. `409` `parts can only be added while in progress` unless the order is `IN_PROGRESS`.
4. `409` `part already added` when the order already has a part with the same name, ignoring upper/lower case (names are compared after trimming).

Then the part is saved and a history entry is recorded with `action` `PART_ADDED` and `detail` `<name> x<quantity>`, for example `Gasket x2`. `201` with the part:

```json
{ "id": 5, "name": "Gasket", "quantity": 2, "unitCostCents": 350 }
```

### GET `/{id}/summary`

What has been used on the order so far:

```json
{
  "orderId": 12,
  "status": "IN_PROGRESS",
  "partLines": 3,
  "totalQuantity": 7,
  "totalCostCents": 4899
}
```

- `partLines`: how many parts the order has.
- `totalQuantity`: the sum of `quantity` over its parts.
- `totalCostCents`: the sum of `quantity` times `unitCostCents` over its parts.

### GET `/{id}/history`

The order's history entries as a list, oldest first, in the order they were recorded:

```json
[
  { "action": "CREATED", "detail": "created", "actor": "dana", "at": "2027-01-02T09:30:00Z" }
]
```

## Running the tests

You need JDK 17 or newer. From the project root:

```
mvnw.cmd test        (Windows)
sh mvnw test         (macOS / Linux)
```

The first run downloads Maven and the project's libraries, so allow a minute and an internet connection. Later runs are faster. There is nothing else to install or start.
