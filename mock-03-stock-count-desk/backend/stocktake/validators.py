import re
from datetime import date

from .models import SESSION_STATUSES

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SORT_KEYS = ("scheduled", "scheduled_desc", "location")
MAX_PER_PAGE = 20


class ValidationFailed(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def _text(value, field, required=False):
    if value is None:
        if required:
            raise ValidationFailed(f"{field} is required")
        return ""
    if not isinstance(value, str):
        raise ValidationFailed(f"{field} must be text")
    value = value.strip()
    if required and not value:
        raise ValidationFailed(f"{field} is required")
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


def clean_new_session(data):
    location = _text(data.get("location"), "location", required=True)
    scheduled_for = parse_date(data.get("scheduled_for"), "scheduled_for")
    assigned_to = None
    if "assigned_to" in data:
        assigned_to = _text(data.get("assigned_to"), "assigned_to", required=True)
    note = _text(data.get("note"), "note")
    return {
        "location": location,
        "scheduled_for": scheduled_for,
        "assigned_to": assigned_to,
    }


def parse_count(data):
    sku = _text(data.get("sku"), "sku", required=True)
    counted = data.get("counted")
    if isinstance(counted, bool) or not isinstance(counted, int):
        raise ValidationFailed("counted must be an integer")
    return sku, counted


def parse_list_params(query):
    status = query.get("status", "").strip()
    if status and status not in SESSION_STATUSES:
        raise ValidationFailed("status is not an allowed value")

    sort = query.get("sort", "").strip() or "scheduled"
    if sort not in SORT_KEYS:
        raise ValidationFailed("sort is not an allowed value")

    scheduled_from = scheduled_to = None
    if query.get("scheduled_from"):
        scheduled_from = parse_date(query["scheduled_from"], "scheduled_from")
    if query.get("scheduled_to"):
        scheduled_to = parse_date(query["scheduled_to"], "scheduled_to")
    if scheduled_from and scheduled_to and scheduled_from > scheduled_to:
        raise ValidationFailed("scheduled_from must not be after scheduled_to")

    page = _int_param(query, "page", 1)
    per_page = _int_param(query, "per_page", 4)
    if page < 1:
        raise ValidationFailed("page must be at least 1")
    if per_page < 1 or per_page > MAX_PER_PAGE:
        raise ValidationFailed(f"per_page must be between 1 and {MAX_PER_PAGE}")

    return {
        "status": status,
        "location": query.get("location", "").strip(),
        "assigned_to": query.get("assigned_to", "").strip(),
        "scheduled_from": scheduled_from,
        "scheduled_to": scheduled_to,
        "q": query.get("q", "").strip(),
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
