# Equipment Loan Desk (React + Django)

An internal tool for a shared equipment cage. A clerk lends out laptops, cameras, audio gear and tools to borrowers, extends loans, takes items back, charges late fees, and reviews what each borrower has used.

The React app lives in `frontend/`, the Django API in `backend/`. The backend is what the tests cover.

## Who is acting

Every request that changes data identifies the acting person with the `X-Clerk` header, which holds that person's username. If the header is missing, the actor is `system`.

## Data

Equipment: `id`, `name` (unique), `category`, `units`, `daily_fee_cents`

- `category`: `laptop`, `camera`, `audio`, `tools`
- `units`: how many of this item the desk owns. `daily_fee_cents` is an integer.
- Units are available unless they are on an `active` loan: available units = `units` minus the total quantity on that equipment's lines in `active` loans. Loans that are `returned` or `cancelled` hold no units.

Loan: `id`, `borrower`, `status`, `checked_out_on`, `due_on`, `returned_on`, `extensions`, `fee_cents`, `created_by`, `created_at`, `items`

- `status`: `active`, `returned`, `cancelled` (new loans are `active`)
- `checked_out_on`, `due_on`, `returned_on`: dates formatted `YYYY-MM-DD`; `returned_on` is `null` until the loan is returned
- `extensions`: how many times the loan has been extended (starts at 0). `fee_cents`: the late fee in cents (starts at 0)
- `items`: the loan lines in the order they were created, each with `equipment_id`, `name`, `category` and `quantity`. A loan has at most one line per piece of equipment.

### Loan period

When a loan is created, `due_on` is `checked_out_on` plus a number of days that depends on the categories on the loan: `laptop` 7, `camera` 3, `audio` 5, `tools` 4. A loan with items from several categories gets the **shortest** of their periods.

### Late fee

A loan returned on or before `due_on` has no fee. A loan returned late has a grace period of 1 day: the number of days late is `returned_on` minus `due_on`, and the chargeable days are the days late minus the 1 grace day (never below 0).

The daily rate is the sum, over the loan's lines, of `quantity` times the equipment's `daily_fee_cents`. The fee is the daily rate times the chargeable days, except that every chargeable day after the 7th costs double.

## Endpoints

### POST /api/loans/

Body: `borrower`, `start` (`YYYY-MM-DD`), `items` (a list of `{"equipment_id": ..., "quantity": ...}`). Checks run in this order:

1. 400 when `borrower` is missing, not text or blank after trimming; when `start` is missing, not formatted `YYYY-MM-DD` or not a real date; when `items` is missing, not a list or empty; or when an entry is not an object, has an `equipment_id` that is not a whole number, has a `quantity` that is not a whole number of at least 1, or repeats an `equipment_id` already used in the list. Only JSON integers count as whole numbers; strings, decimals and booleans are rejected.
2. 404 when an `equipment_id` does not exist.
3. 409 when, for any entry, the `quantity` is more than the available units of that equipment.

The check in step 3 covers the whole request: when it fails, nothing is created. On success the response is 201 with the loan: `borrower` stored trimmed, `checked_out_on` set to `start`, `due_on` as described under the loan period, `status` `active`, `extensions` 0, `fee_cents` 0 and `created_by` set to the acting user.

### GET /api/loans/<id>/

Returns 200 with the loan, including `items`. An unknown id returns 404.

### POST /api/loans/<id>/return/

Body: `{"returned_on": "YYYY-MM-DD"}`. Checks run in this order:

1. 404 for an unknown loan.
2. 400 when `returned_on` is missing, not formatted `YYYY-MM-DD` or not a real date, or when it is before the loan's `checked_out_on`.
3. 409 when the loan is not `active`.

On success `status` becomes `returned`, `returned_on` is set, `fee_cents` is set to the late fee, and the response is 200 with the loan.

### POST /api/loans/<id>/extend/

Body: `{"days": <whole number from 1 to 7>}`. Checks run in this order:

1. 404 for an unknown loan.
2. 400 when `days` is missing or is not a whole number from 1 to 7 (strings, decimals and booleans are rejected).
3. 409 when the loan is not `active`.
4. 409 when the loan has already been extended twice.

On success `due_on` moves later by `days`, `extensions` goes up by one, and the response is 200 with the loan.

### POST /api/loans/<id>/cancel/

404 for an unknown loan. 409 when the loan is not `active`. Otherwise `status` becomes `cancelled` and the response is 200 with the loan.

### GET /api/loans/

Lists loans. Query parameters (all optional, combined with AND):

- `status`: one status or several separated by commas (for example `active,returned`)
- `borrower`: only loans of exactly this borrower
- `equipment`: only loans that have a line for the equipment with this id
- `q`: only loans where the text appears, ignoring case, in the `borrower` or in the name of any piece of equipment on the loan
- `due_from` / `due_to`: dates (`YYYY-MM-DD`); only loans whose `due_on` is on or after / on or before the date; both ends are included
- `overdue_on`: a date (`YYYY-MM-DD`); only `active` loans whose `due_on` is before that date
- `sort`: `due` (default), `newest` or `borrower`
- `page`: default 1
- `per_page`: default 5, maximum 20

Each loan appears at most once in the results, even when several of its lines match `q`.

Ordering by `due`: `due_on` earliest first, ties by `id` lowest first. `newest`: `checked_out_on` latest first, ties by `id` lowest first. `borrower`: A to Z ignoring case, ties by `due_on` earliest first, then `id` lowest first.

```json
{
  "total": 7,
  "page": 3,
  "per_page": 3,
  "pages": 3,
  "results": [ { "id": 7, "borrower": "ed", "status": "active", "due_on": "2026-03-06", "items": [], "...": "..." } ]
}
```

`total` is the number of loans matching the filters, not the number on the current page. `pages` is `total` divided by `per_page`, rounded up, and is 0 when nothing matches. A page past the last one returns an empty `results`.

Returns 400 with `{"error": "..."}` when `status` or `sort` is not an allowed value, when `equipment` is not an integer, when a date is not `YYYY-MM-DD` or is not a real date, when `due_from` is after `due_to`, when `page` or `per_page` is not an integer, when `page` is below 1, or when `per_page` is outside 1 to 20.

### GET /api/summary/

Query parameters `from` and `to` (`YYYY-MM-DD`, both required; 400 if one is missing or malformed, or if `from` is after `to`). Reports on loans whose `checked_out_on` is between `from` and `to`, both ends included, leaving out `cancelled` loans. Rows are grouped by `borrower` exactly as stored. Borrowers with no such loans do not appear. Rows are ordered by `fees_cents` (largest first), ties broken by `borrower` A to Z.

```json
{
  "from": "2026-03-01",
  "to": "2026-03-31",
  "borrowers": [
    { "borrower": "dana", "loans": 3, "units": 5, "late_returns": 1, "fees_cents": 1500 }
  ]
}
```

- `loans`: how many loans the borrower has in the range
- `units`: the sum of `quantity` over the lines of those loans
- `late_returns`: how many of those loans are `returned` with a `fee_cents` above 0
- `fees_cents`: the sum of `fee_cents` over those loans

## Running the tests

From the project root:

```
pip install -r requirements.txt
pytest
```
