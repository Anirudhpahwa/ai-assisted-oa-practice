from datetime import timedelta

LOAN_PERIOD_DAYS = {"laptop": 7, "camera": 3, "audio": 5, "tools": 4}


def loan_days(categories):
    """A loan runs for the shortest period of any category it contains."""
    return max(LOAN_PERIOD_DAYS[category] for category in categories)


def due_date(start, categories):
    return start + timedelta(days=loan_days(categories))
