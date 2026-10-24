from datetime import datetime

from . import dates
from .models import LEAVE_TYPES, STATUSES

DEFAULT_PER_PAGE = 5
MAX_PER_PAGE = 20
DECISIONS = ("approve", "reject")


class ValidationFailed(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def _int_value(value, name):
    if isinstance(value, bool):
        raise ValidationFailed(f"{name} must be an integer")
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationFailed(f"{name} must be an integer")


def parse_date(value, name):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValidationFailed(f"{name} must be formatted as YYYY-MM-DD")


def clean_new_request(data):
    leave_type = data.get("leave_type")
    if leave_type not in LEAVE_TYPES:
        raise ValidationFailed(f"leave_type must be one of {LEAVE_TYPES}")
    start = parse_date(data.get("start_date"), "start_date")
    end = parse_date(data.get("end_date"), "end_date")
    if end < start:
        raise ValidationFailed("end_date cannot be before start_date")
    days = dates.count_weekdays(start, end)
    if days < 1:
        raise ValidationFailed("the range contains no working days")
    reason = data.get("reason", "")
    if not isinstance(reason, str):
        raise ValidationFailed("reason must be a string")
    return {
        "employee_id": _int_value(data.get("employee_id"), "employee_id"),
        "leave_type": leave_type,
        "start_date": start,
        "end_date": end,
        "days": days,
        "reason": reason.strip(),
    }


def parse_decision(data):
    decision = data.get("decision")
    if decision not in DECISIONS:
        raise ValidationFailed(f"decision must be one of {list(DECISIONS)}")
    return decision


def parse_list_params(params):
    status = params.get("status") or None
    if status and status not in STATUSES:
        raise ValidationFailed(f"status must be one of {STATUSES}")
    leave_type = params.get("leave_type") or None
    if leave_type and leave_type not in LEAVE_TYPES:
        raise ValidationFailed(f"leave_type must be one of {LEAVE_TYPES}")
    employee_id = params.get("employee_id")
    page = _int_value(params.get("page", 1), "page")
    per_page = _int_value(params.get("page_size", DEFAULT_PER_PAGE), "per_page")
    if page < 1:
        raise ValidationFailed("page must be positive")
    if per_page < 1 or per_page > MAX_PER_PAGE:
        raise ValidationFailed(f"per_page must be between 1 and {MAX_PER_PAGE}")
    return {
        "employee_id": _int_value(employee_id, "employee_id") if employee_id else None,
        "status": status,
        "leave_type": leave_type,
        "department": (params.get("department") or "").strip(),
        "page": page,
        "per_page": per_page,
    }


def parse_on_date(params):
    return parse_date(params.get("date"), "date")


def parse_year(params):
    return _int_value(params.get("year"), "year")
