# Leave Desk (React + Django)

An internal tool where employees request time off and managers approve or reject it. The desk tracks each employee's annual leave balance, shows who is out on a given day, and reports leave by department.

The React app lives in `frontend/`, the Django API in `backend/`. The backend is what the tests cover.

## Who is acting

Every request that changes data identifies the acting person with the `X-User` header, which holds that person's `username`. If the header is missing, the actor is `system`.

## Data

Employee: `id`, `name`, `username`, `department`, `balance_days`

- `username` is unique. `balance_days` is the annual leave the employee has left, in days.

Leave request: `id`, `employee_id`, `employee_name`, `department`, `leave_type`, `start_date`, `end_date`, `days`, `reason`, `status`, `created_by`, `decided_by`, `decided_at`, `created_at`

- `leave_type`: `annual`, `sick`, `unpaid`
- `status`: `pending`, `approved`, `rejected`, `cancelled` (new requests are `pending`)
- `start_date` / `end_date`: dates formatted `YYYY-MM-DD`, both days included
- `days`: the number of weekdays (Monday to Friday) from `start_date` to `end_date`, both included. Weekends do not count and there are no holidays.
- `reason`: free text, default empty string
- `decided_by` / `decided_at`: empty string / `null` until the request is approved or rejected

Only `annual` leave uses the employee's `balance_days`. `sick` and `unpaid` leave never change it.

## Endpoints

### GET /api/employees/<id>/

Returns 200 with the employee. An unknown id returns 404.

### POST /api/leave/

Body: `employee_id`, `leave_type`, `start_date`, `end_date`, optional `reason`. Checks run in this order:

1. 400 when `employee_id` is not an integer, `leave_type` is not allowed, a date is missing or not `YYYY-MM-DD`, `end_date` is before `start_date`, or the range contains no weekdays.
2. 404 when the employee does not exist.
3. 409 when the employee already has a `pending` or `approved` request that shares at least one calendar day with the new range. Requests that are `rejected` or `cancelled` never conflict.

On success the response is 201 with the request, status `pending`, `days` as described above, and `created_by` set to the acting user.

### POST /api/leave/<id>/decision/

Body: `{"decision": "approve"}` or `{"decision": "reject"}`. Checks run in this order:

1. 404 for an unknown request.
2. 400 when `decision` is missing or is neither `approve` nor `reject`.
3. 403 when the acting user is the employee the request belongs to (a person cannot decide their own request).
4. 409 when the request is not `pending`.
5. 409 when approving an `annual` request and the employee's `balance_days` is lower than the request's `days`.

On success, `approve` sets the status to `approved` and `reject` sets it to `rejected`. Approving an `annual` request subtracts `days` from the employee's `balance_days`; every other decision leaves the balance alone. `decided_by` is set to the acting user and `decided_at` to the current time. The response is 200 with the request.

### POST /api/leave/<id>/cancel/

Cancels a request. Checks run in this order:

1. 404 for an unknown request.
2. 403 when the acting user is not the employee the request belongs to.
3. 409 when the request is not `pending` or `approved`.

On success the status becomes `cancelled`. Cancelling an `approved` `annual` request gives its `days` back to the employee's `balance_days`. Cancelling a `pending` request, or a `sick` or `unpaid` request, leaves the balance alone. The response is 200 with the request.

### GET /api/leave/

Lists requests. Query parameters (all optional, combined with AND):

- `employee_id`: only this employee's requests
- `status`: only requests with this status
- `leave_type`: only requests of this type
- `department`: only requests of employees in this department
- `page`: default 1
- `per_page`: default 5, maximum 20

Requests are ordered by `start_date` (earliest first), ties broken by `id` (lowest first).

```json
{
  "total": 7,
  "page": 3,
  "per_page": 3,
  "pages": 3,
  "results": [ { "id": 7, "employee_id": 2, "employee_name": "Ben Ortiz", "department": "eng", "leave_type": "unpaid", "start_date": "2026-04-13", "end_date": "2026-04-14", "days": 2, "reason": "", "status": "rejected", "created_by": "system", "decided_by": "", "decided_at": null, "created_at": "..." } ]
}
```

`total` is the number of requests matching the filters, not the number on the current page. `pages` is `total` divided by `per_page`, rounded up, and is 0 when nothing matches.

Returns 400 with `{"error": "..."}` when `status` or `leave_type` is not an allowed value, when `employee_id`, `page` or `per_page` is not an integer, when `page` is below 1, or when `per_page` is outside 1 to 20.

### GET /api/leave/out/

Query parameter `date` (`YYYY-MM-DD`, required; 400 if missing or malformed). Returns the requests with status `approved` whose range includes that date, with both the first and last day included. They are ordered by the employee's name (A to Z), ties broken by lowest `id`.

```json
{ "date": "2026-03-11", "results": [ { "id": 4, "employee_name": "Adam Cole", "...": "..." } ] }
```

### GET /api/leave/summary/

Query parameter `year` (an integer, required; 400 otherwise). Reports on requests whose `start_date` falls in that calendar year, grouped by the employee's department, ordered by department name. Only departments with at least one such request appear.

```json
{
  "year": 2026,
  "departments": [
    {
      "department": "eng",
      "approved_days": 10,
      "people_out": 2,
      "requests": { "pending": 1, "approved": 3, "rejected": 0, "cancelled": 1 }
    }
  ]
}
```

- `approved_days`: the sum of `days` over the department's `approved` requests, 0 if there are none
- `people_out`: how many different employees in the department have at least one `approved` request
- `requests`: how many requests the department has in each status, with all four statuses always present

## Running the tests

From the project root:

```
pip install -r requirements.txt
pytest
```
