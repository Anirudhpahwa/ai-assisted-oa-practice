from django.utils import timezone

from . import dates
from .models import PRIORITIES, Ticket


def sla_report(start, end):
    """Per-priority resolution report for tickets created between start and end."""
    low, high = dates.day_bounds(start, end)
    now = timezone.now()
    rows = {
        name: {"priority": name, "tickets": 0, "resolved": 0, "breached": 0, "minutes": []}
        for name in reversed(PRIORITIES)
    }
    for ticket in Ticket.objects.filter(created_at__gte=low, created_at__lt=high):
        row = rows[ticket.priority]
        row["tickets"] += 1
        if ticket.resolved_at:
            row["resolved"] += 1
            row["minutes"].append((ticket.resolved_at - ticket.created_at).total_seconds() / 60)
            row["breached"] += ticket.resolved_at > ticket.due_at
        else:
            row["breached"] += ticket.due_at < now
    result = []
    for row in rows.values():
        minutes = row.pop("minutes")
        row["avg_resolution_minutes"] = round(sum(minutes) / len(minutes)) if minutes else None
        result.append(row)
    return result
