import re
from datetime import date

from .models import PRIORITIES, STATUSES

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SORT_KEYS = ("newest", "due", "priority")
MAX_PER_PAGE = 25
MAX_TITLE = 80


class ValidationFailed(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def _strict_text(value, field):
    if not isinstance(value, str):
        raise ValidationFailed(f"{field} must be text")
    return value.strip()


def _title(value):
    title = _strict_text(value, "title") if value is not None else ""
    if not title:
        raise ValidationFailed("title is required")
    if len(title) > MAX_TITLE:
        raise ValidationFailed(f"title must be at most {MAX_TITLE} characters")
    return title


def _requester(value):
    requester = _strict_text(value, "requester") if value is not None else ""
    if not requester:
        raise ValidationFailed("requester is required")
    return requester


def _priority(value):
    if value not in PRIORITIES:
        raise ValidationFailed("priority is not an allowed value")
    return value


def parse_date(value, field):
    if not isinstance(value, str) or not DATE_PATTERN.match(value):
        raise ValidationFailed(f"{field} must be a date formatted YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValidationFailed(f"{field} is not a real date")


def _int_param(query, name, default):
    raw = query.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        raise ValidationFailed(f"{name} must be an integer")


def clean_new_ticket(data):
    return {
        "title": _title(data.get("title")),
        "description": _strict_text(data.get("description", ""), "description"),
        "requester": _requester(data.get("requester")),
        "priority": _priority(data.get("priority", "normal")),
    }


def clean_ticket_update(data):
    changes = {}
    if "title" in data:
        changes["title"] = _title(data["title"])
    changes["description"] = _strict_text(data.get("description", ""), "description")
    if "priority" in data:
        changes["priority"] = _priority(data["priority"])
    if "assignee" in data:
        changes["assignee"] = _strict_text(data["assignee"], "assignee")
    return changes


def parse_status(data):
    status = data.get("status")
    if status not in STATUSES:
        raise ValidationFailed("status is not an allowed value")
    return status


def parse_comment(data):
    body = data.get("body")
    if not isinstance(body, str) or not body.strip():
        raise ValidationFailed("body is required")
    internal = data.get("internal", False)
    if not isinstance(internal, bool):
        raise ValidationFailed("internal must be true or false")
    return body.strip(), internal


def parse_list_params(query):
    statuses = [s.strip() for s in query.get("status", "").split(",") if s.strip()]
    if any(s not in STATUSES for s in statuses):
        raise ValidationFailed("status is not an allowed value")

    priority = query.get("priority", "").strip()
    if priority and priority not in PRIORITIES:
        raise ValidationFailed("priority is not an allowed value")

    overdue = query.get("overdue")
    if overdue not in (None, "", "true"):
        raise ValidationFailed("overdue must be true")

    sort = query.get("sort", "").strip() or "newest"
    if sort not in SORT_KEYS:
        raise ValidationFailed("sort is not an allowed value")

    created_from = created_to = None
    if query.get("created_from"):
        created_from = parse_date(query["created_from"], "created_from")
    if query.get("created_to"):
        created_to = parse_date(query["created_to"], "created_to")
    if created_from and created_to and created_from > created_to:
        raise ValidationFailed("created_from must not be after created_to")

    page = _int_param(query, "page", 1)
    per_page = _int_param(query, "per_page", 5)
    if page < 1:
        raise ValidationFailed("page must be at least 1")
    if per_page < 1 or per_page > MAX_PER_PAGE:
        raise ValidationFailed(f"per_page must be between 1 and {MAX_PER_PAGE}")

    return {
        "statuses": statuses,
        "priority": priority,
        "assignee": query.get("assignee", "").strip(),
        "requester": query.get("requester", "").strip(),
        "q": query.get("q", "").strip(),
        "created_from": created_from,
        "created_to": created_to,
        "overdue": overdue == "true",
        "sort": sort,
        "page": page,
        "per_page": per_page,
    }


def parse_range(query):
    start = parse_date(query.get("from"), "from")
    end = parse_date(query.get("to"), "to")
    if start > end:
        raise ValidationFailed("from must not be after to")
    return start, end
