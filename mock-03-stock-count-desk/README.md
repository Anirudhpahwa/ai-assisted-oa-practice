# Stock Count Desk (React + Django)

An internal tool for warehouse cycle counts. A manager schedules a count session for a storage location, the assigned counter records the quantity found for each product, submits the session, and a different person approves it, which updates the stock levels. The desk also reports shortages by location.

The React app lives in `frontend/`, the Django API in `backend/`. The backend is what the tests cover.

## Who is acting

Every request that changes data identifies the acting person with the `X-Staff` header, which holds that person's username. If the header is missing, the actor is `system`.

## Data

Product: `id`, `sku`, `name`, `on_hand`, `unit_cost_cents`

- `sku` is unique. `on_hand` is the quantity the system believes is in stock. `unit_cost_cents` is an integer.

Count session: `id`, `location`, `scheduled_for`, `assigned_to`, `status`, `note`, `created_by`, `submitted_at`, `approved_by`, `approved_at`, `line_count`, `created_at`

- `status`: `open`, `submitted`, `approved`, `voided` (new sessions are `open`)
- `scheduled_for`: a date formatted `YYYY-MM-DD`
- `assigned_to`: username of the counter
- `note`: free text, default empty string
- `submitted_at` / `approved_at`: `null` until that happens; `approved_by` is an empty string until the session is approved
- `line_count`: the number of count lines the session has

Count line: `id`, `sku`, `product_name`, `expected`, `counted`, `variance`, `counted_by`, `updated_at`

- `expected`: the product's `on_hand` at the moment the product is first counted in the session. It never changes afterwards.
- `counted`: the quantity found, an integer of 0 or more
- `variance` = `counted` - `expected`
- A session has at most one line per product.

## Endpoints

### POST /api/sessions/

Body: `location`, `scheduled_for`, optional `assigned_to`, optional `note`. Checks run in this order:

1. 400 when `location` is missing or blank after trimming, when `scheduled_for` is missing, is not formatted `YYYY-MM-DD` or is not a real date, when `assigned_to` is present but not text or blank after trimming, or when `note` is present but not text.
2. 409 when another session at the same location is `open` or `submitted`. Locations are compared ignoring case, after trimming. Sessions that are `approved` or `voided` never conflict.

On success the response is 201 with the session: `location`, `assigned_to` and `note` are stored trimmed, `assigned_to` defaults to the acting user, `status` is `open`, `created_by` is the acting user and `line_count` is 0.

### GET /api/sessions/<id>/

Returns 200 with the session plus a `lines` list ordered by `sku` (A to Z). An unknown id returns 404.

### POST /api/sessions/<id>/lines/

Records a counted quantity. Body: `sku`, `counted`. Checks run in this order:

1. 404 for an unknown session.
2. 400 when `sku` is missing or blank, or when `counted` is not a whole number or is below 0. Only JSON integers count as whole numbers; strings, decimals and booleans are rejected.
3. 404 when no product has that `sku`.
4. 403 when the acting user is not the session's `assigned_to`.
5. 409 when the session is not `open`.

The first time a product is counted in a session a new line is created and the response is 201. Counting the same product again updates that line (its `counted` and `counted_by`, with `variance` following from the line's own `expected`) and the response is 200. `counted_by` is the acting user. The response is the line.

### POST /api/sessions/<id>/submit/

Checks run in this order: 404 for an unknown session; 403 when the acting user is not the session's `assigned_to`; 409 when the session is not `open`; 409 when the session has no lines. On success `status` becomes `submitted`, `submitted_at` is set, and the response is 200 with the session.

### POST /api/sessions/<id>/approve/

Checks run in this order: 404 for an unknown session; 403 when the acting user is the session's `assigned_to` (a counter cannot approve their own count); 409 when the session is not `submitted`.

On success every line's product has its `on_hand` replaced by the line's `counted` quantity, whatever `on_hand` was in the meantime. `status` becomes `approved`, `approved_by` is the acting user, `approved_at` is set, and the response is 200 with the session.

### POST /api/sessions/<id>/void/

Any user may void a session. 404 for an unknown session. 409 when the session is `approved` or already `voided`. Otherwise `status` becomes `voided`, stock levels are left alone, and the response is 200 with the session.

### GET /api/sessions/

Lists sessions. Query parameters (all optional, combined with AND):

- `status`: only sessions with this status. Without it, `voided` sessions are left out of the list.
- `location`: only sessions at this location, ignoring case
- `assigned_to`: only sessions assigned to exactly this username
- `scheduled_from` / `scheduled_to`: only sessions whose `scheduled_for` is on or after / on or before the date (`YYYY-MM-DD`); both ends are included
- `q`: only sessions where the text appears, ignoring case, in the `location` or in the `note`
- `sort`: `scheduled` (default), `scheduled_desc` or `location`
- `page`: default 1
- `per_page`: default 4, maximum 20

Ordering by `scheduled`: `scheduled_for` earliest first, ties by `id` lowest first. `scheduled_desc`: `scheduled_for` latest first, ties by `id` lowest first. `location`: A to Z ignoring case, ties by `id` lowest first.

```json
{
  "total": 7,
  "page": 3,
  "per_page": 3,
  "pages": 3,
  "results": [ { "id": 7, "location": "Cold Room", "scheduled_for": "2026-03-01", "assigned_to": "ivy", "status": "open", "note": "", "line_count": 0, "...": "..." } ]
}
```

`total` is the number of sessions matching the filters, not the number on the current page. `pages` is `total` divided by `per_page`, rounded up, and is 0 when nothing matches. A page past the last one returns an empty `results`.

Returns 400 with `{"error": "..."}` when `status` or `sort` is not an allowed value, when a date is not `YYYY-MM-DD` or is not a real date, when `scheduled_from` is after `scheduled_to`, when `page` or `per_page` is not an integer, when `page` is below 1, or when `per_page` is outside 1 to 20.

### GET /api/summary/

Query parameters `from` and `to` (`YYYY-MM-DD`, both required; 400 if one is missing or malformed, or if `from` is after `to`). Reports on lines of `approved` sessions whose `scheduled_for` is between `from` and `to`, both ends included, grouped by the session's `location` exactly as stored. Locations with no such lines do not appear. They are ordered by `shortage_value_cents` (largest first), ties broken by `location` A to Z.

```json
{
  "from": "2026-03-01",
  "to": "2026-04-01",
  "locations": [
    { "location": "Dock 2", "sessions": 1, "lines": 1, "net_units": -3, "shortage_units": 3, "shortage_value_cents": 1500 }
  ]
}
```

- `sessions`: how many different approved sessions the location has in the range
- `lines`: how many count lines those sessions have
- `net_units`: the sum of `variance` over those lines
- `shortage_units`: the sum of the shortfall, `-variance`, over the lines whose `variance` is below 0; 0 if there are none
- `shortage_value_cents`: for the lines whose `variance` is below 0, the sum of the shortfall times the product's `unit_cost_cents`; 0 if there are none

## Running the tests

From the project root:

```
pip install -r requirements.txt
pytest
```
