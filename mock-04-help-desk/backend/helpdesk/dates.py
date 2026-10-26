from datetime import datetime, time, timezone


def day_start(day):
    return datetime.combine(day, time.min, tzinfo=timezone.utc)


def day_bounds(first_day, last_day):
    """Half-open datetime range [low, high) covering whole UTC days; either end may be None."""
    low = day_start(first_day) if first_day else None
    high = day_start(last_day) if last_day else None
    return low, high
