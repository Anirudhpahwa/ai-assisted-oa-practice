from datetime import timedelta


def count_weekdays(start, end):
    """Number of Monday-to-Friday days from start to end."""
    total = 0
    day = start
    while day < end:
        if day.weekday() < 5:
            total += 1
        day += timedelta(days=1)
    return total
