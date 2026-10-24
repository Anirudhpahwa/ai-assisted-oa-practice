from .models import LeaveRequest


def find_conflict(employee, start, end):
    """Return an existing request of this employee that shares a day with start..end."""
    return LeaveRequest.objects.filter(
        employee=employee,
        start_date__lte=end,
        end_date__gte=start,
    ).first()
