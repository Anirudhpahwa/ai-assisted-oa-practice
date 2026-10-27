import re
from datetime import date

from .models import LOAN_STATUSES

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SORT_KEYS = ("due", "newest", "borrower")
MAX_PER_PAGE = 20
MAX_EXTEND_DAYS = 7


class ValidationFailed(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


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


def _items(value):
    if not isinstance(value, list) or not value:
        raise ValidationFailed("items must be a non-empty list")
    cleaned = []
    seen = set()
    for entry in value:
        if not isinstance(entry, dict):
            raise ValidationFailed("each item must be an object")
        equipment_id = entry.get("equipment_id")
        if not _is_int(equipment_id):
            raise ValidationFailed("equipment_id must be an integer")
        quantity = entry.get("quantity")
        if not isinstance(quantity, int) or quantity < 1:
            raise ValidationFailed("quantity must be a whole number of at least 1")
        if equipment_id in seen:
            raise ValidationFailed("each piece of equipment may appear only once")
        seen.add(equipment_id)
        cleaned.append({"equipment_id": equipment_id, "quantity": quantity})
    return cleaned


def clean_new_loan(data):
    borrower = data.get("borrower")
    if not isinstance(borrower, str) or not borrower.strip():
        raise ValidationFailed("borrower is required")
    return {
        "borrower": borrower.strip(),
        "start": parse_date(data.get("start"), "start"),
        "items": _items(data.get("items")),
    }


def parse_return(data):
    return parse_date(data.get("returned_on"), "returned_on")


def parse_extend(data):
    days = data.get("days")
    if not _is_int(days) or days < 1 or days > MAX_EXTEND_DAYS:
        raise ValidationFailed(f"days must be a whole number from 1 to {MAX_EXTEND_DAYS}")
    return days


def parse_list_params(query):
    statuses = [s.strip() for s in query.get("status", "").split(",") if s.strip()]
    if any(s not in LOAN_STATUSES for s in statuses):
        raise ValidationFailed("status is not an allowed value")

    sort = query.get("sort", "").strip() or "due"
    if sort not in SORT_KEYS:
        raise ValidationFailed("sort is not an allowed value")

    equipment_id = _int_param(query, "equipment", None)

    due_from = due_to = overdue_on = None
    if query.get("due_from"):
        due_from = parse_date(query["due_from"], "due_from")
    if query.get("due_to"):
        due_to = parse_date(query["due_to"], "due_to")
    if due_from and due_to and due_from > due_to:
        raise ValidationFailed("due_from must not be after due_to")
    if query.get("overdue_on"):
        overdue_on = parse_date(query["overdue_on"], "overdue_on")

    page = _int_param(query, "page", 1)
    per_page = _int_param(query, "per_page", 5)
    if page < 1:
        raise ValidationFailed("page must be at least 1")
    if per_page < 1 or per_page > MAX_PER_PAGE:
        raise ValidationFailed(f"per_page must be between 1 and {MAX_PER_PAGE}")

    return {
        "statuses": statuses,
        "borrower": query.get("borrower", "").strip(),
        "equipment_id": equipment_id,
        "q": query.get("q", "").strip(),
        "due_from": due_from,
        "due_to": due_to,
        "overdue_on": overdue_on,
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
