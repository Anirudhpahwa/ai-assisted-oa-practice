from datetime import timedelta

SLA_HOURS = {"urgent": 4, "high": 12, "normal": 24, "low": 72}


def due_at_for(created_at, priority):
    """Resolution deadline for a ticket created at `created_at`."""
    return created_at + timedelta(hours=SLA_HOURS[priority])
