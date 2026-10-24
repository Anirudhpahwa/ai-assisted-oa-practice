# Returns Desk (React + Django)

A back-office tool for a retailer's returns team. Agents log a customer's return request, add the returned items, move the request through an approval workflow, and watch a filterable list and a summary of everything in flight.

The React app lives in `frontend/`, the Django API in `backend/`. The backend is what the tests cover.

## Who is acting

Every request that changes data identifies the acting agent with the `X-Agent` header. If the header is missing, the agent is `system`.

## Data

Return: `id`, `customer`, `order_number`, `reason`, `note`, `status`, `refund_total_cents`, `created_by`, `decided_by`, `decided_at`, `created_at`

- `reason`: `damaged`, `wrong_item`, `not_needed`, `other` (default `other`)
- `status`: `requested`, `approved`, `received`, `refunded`, `rejected`, `cancelled` (default `requested`)
- `note`: free text, default empty string
- `refund_total_cents`: integer, default 0, see "Refund total" below
- `created_by`: the acting agent when the return was created
- `decided_by` / `decided_at`: empty string / `null` until the return is approved or rejected

Item: `id`, `return_id`, `sku`, `quantity`, `unit_price_cents`, `line_total_cents`

- `quantity`: integer from 1 to 20, both ends included
- `unit_price_cents`: integer, 0 or more
- `line_total_cents` = `quantity` x `unit_price_cents`

Status event: `from_status`, `to_status`, `actor`, `created_at`

### Refund total

The subtotal of a return is the sum of the `line_total_cents` of its items. When the return's `reason` is `not_needed`, a restock fee of 10% of the subtotal is withheld, rounded half up to a whole cent, and `refund_total_cents` is the subtotal minus that fee. For any other reason `refund_total_cents` equals the subtotal. The value is kept up to date whenever an item is added.

## Endpoints

### POST /api/returns/

Creates a return. `customer` and `order_number` are required; each is 400 if missing or blank after trimming. `reason` and `note` are optional. A `reason` outside the allowed values returns 400. Surrounding whitespace is trimmed from stored text. Returns 201 with the return, status `requested`, and `created_by` set to the acting agent.

### GET /api/returns/<id>/

Returns 200 with the return plus an `items` list and a `history` list of status events, oldest first. An unknown id returns 404.

### POST /api/returns/<id>/items/

Body: `{"sku": "...", "quantity": 2, "unit_price_cents": 1250}`. Checks run in this order:

1. Unknown return: 404.
2. `sku` missing or blank after trimming, `quantity` or `unit_price_cents` not an integer, `quantity` outside 1 to 20, or a negative `unit_price_cents`: 400.
3. The return's status is not `requested`: 409.

On success the refund total is updated and the response is 201 with the item.

### POST /api/returns/<id>/transition/

Body: `{"to": "approved"}`. Moves the return to a new status. Checks run in this order:

1. Unknown return: 404.
2. `to` missing or not one of the six statuses: 400.
3. The move is not allowed from the current status: 409.
4. The move is to `approved` and the return has no items: 409.

Allowed moves:

| From | To |
|---|---|
| `requested` | `approved`, `rejected`, `cancelled` |
| `approved` | `received`, `cancelled` |
| `received` | `refunded` |
| `refunded`, `rejected`, `cancelled` | none |

On success the status is saved, one status event is recorded (`from_status`, `to_status` and the acting agent as `actor`), and the response is 200 with the return. When the new status is `approved` or `rejected`, `decided_at` is set to the current time and `decided_by` to the acting agent.

### GET /api/returns/

Lists returns. Query parameters (all optional, combined with AND):

- `status`: only returns with this status
- `reason`: only returns with this reason
- `q`: case-insensitive search. A return matches when `q` appears anywhere in its `customer`, its `order_number` or its `note`.
- `sort`: `newest` (default, highest id first), `oldest` (lowest id first), or `refund_desc` (highest `refund_total_cents` first, ties broken by lowest id first)
- `limit`: default 4, minimum 1, maximum 25
- `offset`: default 0

Cancelled returns are left out of the list unless `status=cancelled` is given.

Response:

```json
{
  "total": 6,
  "limit": 4,
  "offset": 4,
  "has_more": false,
  "results": [ { "id": 2, "customer": "Dana Whitfield", "order_number": "SO-48213", "reason": "damaged", "note": "", "status": "requested", "refund_total_cents": 2500, "created_by": "priya", "decided_by": "", "decided_at": null, "created_at": "..." } ]
}
```

`total` is the number of returns matching the filters, not the number on the current page. `has_more` is true when there are matching returns after the ones in `results`.

Returns 400 with `{"error": "..."}` when `status`, `reason` or `sort` has a value that is not allowed, when `limit` or `offset` is not an integer, when `limit` is outside 1 to 25, or when `offset` is negative.

### GET /api/returns/summary/

Counts returns by status. Optional `reason` limits the summary to that reason (400 if the value is not allowed). Cancelled returns are included here.

```json
{
  "by_status": {
    "requested": 2, "approved": 1, "received": 1,
    "refunded": 2, "rejected": 1, "cancelled": 1
  },
  "open_count": 4,
  "refunded_total_cents": 3500
}
```

`by_status` always has all six statuses, with 0 for a status that has no returns. `open_count` is the number of returns that are `requested`, `approved` or `received`. `refunded_total_cents` is the sum of `refund_total_cents` over returns with status `refunded`.

## Running the tests

From the project root:

```
pip install -r requirements.txt
pytest
```
