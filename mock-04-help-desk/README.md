# Help Desk (React + Django)

An internal tool for a support team. Agents log tickets for requesters, assign them, move them through a status workflow, exchange comments, and watch how well resolution deadlines are met.

The React app lives in `frontend/`, the Django API in `backend/`. The backend is what the tests cover.

## Who is acting

Every request that changes data identifies the acting person with the `X-Agent` header, which holds that person's username. If the header is missing, the actor is `system`.

## Data

Ticket: `id`, `title`, `description`, `requester`, `priority`, `status`, `assignee`, `due_at`, `resolved_at`, `created_by`, `created_at`, `updated_at`

- `priority`: `low`, `normal`, `high`, `urgent` (default `normal`)
- `status`: `open`, `in_progress`, `waiting`, `resolved`, `closed` (new tickets are `open`)
- `title`: required, at most 80 characters after trimming. `description`: free text, default empty string.
- `requester`: the username of the person who asked for help. `assignee`: username of the agent working on it; an empty string means unassigned.
- `due_at`: the resolution deadline, `created_at` plus a number of hours that depends on the priority: `urgent` 4, `high` 8, `normal` 24, `low` 72. When the priority changes, `due_at` is recalculated from the ticket's `created_at` and the new priority.
- `resolved_at`: `null` until the ticket is resolved.

Comment: `id`, `author`, `body`, `internal`, `created_at`

History event: `id`, `kind` (`status`, `priority` or `assignee`), `from_value`, `to_value`, `actor`, `created_at`

## Endpoints

### POST /api/tickets/

Body: `title`, `requester`, optional `description`, optional `priority`. Optional header `Idempotency-Key`. Checks run in this order:

1. 400 when `title` is missing, blank after trimming or longer than 80 characters; when `requester` is missing or blank after trimming; when `priority` is not an allowed value; or when `description` is present but not text.
2. When the header is present and not blank, and a ticket was already created with that same key, nothing is created and the response is 200 with that existing ticket, even if the body is different.

On success the response is 201 with the ticket: `title`, `description` and `requester` stored trimmed, `status` `open`, `assignee` empty, `created_by` set to the acting user, and `due_at` as described above. The key is remembered with the ticket.

### GET /api/tickets/<id>/

Returns 200 with the ticket plus `comments` (oldest first, ties by `id` lowest first) and `history` (oldest first, ties by `id` lowest first). An unknown id returns 404.

### PATCH /api/tickets/<id>/

Body: any of `title`, `description`, `priority`, `assignee`. Fields that are not in the body are left as they are. Checks run in this order:

1. 404 for an unknown ticket.
2. 400 when `title` is blank after trimming or longer than 80 characters, when `priority` is not an allowed value, or when `description` or `assignee` is present but not text.
3. 409 when the ticket is `closed`.

`description` and `assignee` are stored trimmed; an `assignee` of `""` unassigns the ticket. For `priority` and `assignee`, a history event is recorded only when the value actually changes: `kind` is the field name, `from_value` and `to_value` are the old and new values, and `actor` is the acting user. A changed `priority` also recalculates `due_at`. The response is 200 with the ticket.

### POST /api/tickets/<id>/status/

Body: `{"status": "<new status>"}`. Checks run in this order:

1. 404 for an unknown ticket.
2. 400 when `status` is missing or is not an allowed value.
3. 409 when the move is not allowed. Allowed moves: `open` to `in_progress` or `resolved`; `in_progress` to `open`, `waiting` or `resolved`; `waiting` to `in_progress` or `resolved`; `resolved` to `open` or `closed`; nothing moves out of `closed`.
4. 409 when moving to `resolved` and the ticket has no assignee.

On success the status changes and a history event of `kind` `status` is recorded. Moving to `resolved` sets `resolved_at` to the current time. Moving from `resolved` back to `open` (a reopen) clears `resolved_at` to `null`; moving from `resolved` to `closed` keeps it. The response is 200 with the ticket.

### POST /api/tickets/<id>/comments/

Body: `body`, optional `internal` (default `false`). Checks run in this order:

1. 404 for an unknown ticket.
2. 400 when `body` is missing or blank after trimming, or when `internal` is present but not `true` or `false`.
3. 409 when the ticket is `closed`.

On success the comment is stored with the trimmed `body` and the acting user as `author`, and the response is 201 with the comment. Customer reply rule: when the ticket is `waiting`, the comment is not internal and its `author` is the ticket's `requester`, the ticket moves to `in_progress` and a `status` history event is recorded with the author as `actor`.

### GET /api/tickets/

Lists tickets. Query parameters (all optional, combined with AND):

- `status`: one status or several separated by commas (for example `open,waiting`)
- `priority`: only this priority
- `assignee`: only tickets assigned to exactly this username; the value `none` means tickets with no assignee
- `requester`: only tickets from exactly this requester
- `q`: only tickets where the text appears, ignoring case, in the `title` or in the `description`
- `created_from` / `created_to`: dates (`YYYY-MM-DD`); only tickets created on or after the start of the first day and before the end of the last day, in UTC. Both days are included in full.
- `overdue`: `true` keeps only tickets whose `due_at` has already passed and whose status is neither `resolved` nor `closed`
- `sort`: `newest` (default), `due` or `priority`
- `page`: default 1
- `per_page`: default 5, maximum 25

Ordering by `newest`: `created_at` latest first, ties by `id` lowest first. `due`: `due_at` earliest first, ties by `id` lowest first. `priority`: `urgent`, then `high`, `normal`, `low`; ties by `due_at` earliest first, then `id` lowest first.

```json
{
  "total": 7,
  "page": 2,
  "per_page": 5,
  "pages": 2,
  "results": [ { "id": 3, "title": "VPN keeps dropping", "priority": "high", "status": "open", "assignee": "", "due_at": "...", "...": "..." } ]
}
```

`total` is the number of tickets matching the filters, not the number on the current page. `pages` is `total` divided by `per_page`, rounded up, and is 0 when nothing matches. A page past the last one returns an empty `results`.

Returns 400 with `{"error": "..."}` when `status` has a value that is not allowed, when `priority`, `sort` or `overdue` (anything but `true`) is not allowed, when a date is not `YYYY-MM-DD` or is not a real date, when `created_from` is after `created_to`, when `page` or `per_page` is not an integer, when `page` is below 1, or when `per_page` is outside 1 to 25.

### GET /api/report/

Query parameters `from` and `to` (`YYYY-MM-DD`, both required; 400 if one is missing or malformed, or if `from` is after `to`). Reports on tickets created between the start of `from` and the end of `to`, in UTC, with both days included in full. The result always has one entry for each priority, in the order `urgent`, `high`, `normal`, `low`.

```json
{
  "from": "2026-03-01",
  "to": "2026-03-31",
  "priorities": [
    { "priority": "urgent", "tickets": 3, "resolved": 2, "breached": 1, "avg_resolution_minutes": 91 }
  ]
}
```

- `tickets`: how many tickets of that priority were created in the range
- `resolved`: how many of them have a `resolved_at`
- `breached`: how many of them are late: either `resolved_at` is after `due_at`, or there is no `resolved_at` and `due_at` has already passed
- `avg_resolution_minutes`: the average time in minutes from `created_at` to `resolved_at` over the resolved tickets, rounded half up to a whole number (90.5 becomes 91); `null` when none are resolved

## Running the tests

From the project root:

```
pip install -r requirements.txt
pytest
```
