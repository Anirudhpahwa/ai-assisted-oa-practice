from .models import REASONS, STATUSES

DEFAULT_LIMIT = 4
MAX_LIMIT = 25
SORT_OPTIONS = ["newest", "oldest", "refund_desc"]


class ValidationFailed(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def _required_text(data, field):
    value = data.get(field)
    if not isinstance(value, str) or not value:
        raise ValidationFailed(f"{field} is required")
    return value.strip()


def _int_value(data, field):
    value = data.get(field)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationFailed(f"{field} must be an integer")
    return value


def clean_new_return(data):
    cleaned = {
        "customer": _required_text(data, "customer"),
        "order_number": _required_text(data, "order_number"),
    }
    if "reason" in data:
        if data["reason"] not in REASONS:
            raise ValidationFailed(f"reason must be one of {REASONS}")
        cleaned["reason"] = data["reason"]
    if "note" in data:
        if not isinstance(data["note"], str):
            raise ValidationFailed("note must be a string")
        cleaned["note"] = data["note"].strip()
    return cleaned


def clean_item(data):
    sku = _required_text(data, "sku")
    quantity = _int_value(data, "quantity")
    if quantity < 1 or quantity > 20:
        raise ValidationFailed("quantity must be between 1 and 20")
    unit_price = _int_value(data, "unit_price_cents")
    if unit_price < 0:
        raise ValidationFailed("unit_price_cents cannot be negative")
    return {"sku": sku, "quantity": quantity, "unit_price_cents": unit_price}


def parse_target_status(data):
    target = data.get("to")
    if target not in STATUSES:
        raise ValidationFailed(f"to must be one of {STATUSES}")
    return target


def parse_reason_filter(value):
    if value and value not in REASONS:
        raise ValidationFailed(f"reason must be one of {REASONS}")
    return value or None


def parse_list_params(params):
    status = params.get("status") or None
    if status and status not in STATUSES:
        raise ValidationFailed(f"status must be one of {STATUSES}")
    sort = params.get("sort", "newest")
    if sort not in SORT_OPTIONS:
        raise ValidationFailed(f"sort must be one of {SORT_OPTIONS}")
    try:
        limit = int(params.get("limit", DEFAULT_LIMIT))
        offset = int(params.get("skip", 0))
    except ValueError:
        raise ValidationFailed("limit and offset must be integers")
    if limit < 1 or limit > MAX_LIMIT:
        raise ValidationFailed(f"limit must be between 1 and {MAX_LIMIT}")
    if offset < 0:
        raise ValidationFailed("offset cannot be negative")
    return {
        "status": status,
        "reason": parse_reason_filter(params.get("reason")),
        "q": (params.get("q") or "").strip(),
        "sort": sort,
        "limit": limit,
        "offset": offset,
    }
