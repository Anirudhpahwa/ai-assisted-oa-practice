GRACE_DAYS = 1
DOUBLE_AFTER_DAYS = 7


def daily_rate(lines):
    return sum(line.quantity * line.equipment.daily_fee_cents for line in lines)


def chargeable_days(due_on, returned_on):
    late = (returned_on - due_on).days
    if late <= GRACE_DAYS:
        return 0
    return late


def late_fee(lines, due_on, returned_on):
    """Fee in cents; chargeable days after the seventh cost double."""
    days = chargeable_days(due_on, returned_on)
    rate = daily_rate(lines)
    normal = min(days, DOUBLE_AFTER_DAYS)
    doubled = days - normal
    return rate * normal + rate * 2 * doubled
