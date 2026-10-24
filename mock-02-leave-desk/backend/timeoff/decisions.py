from django.utils import timezone

from .models import ACTIVE_STATUSES


class DecisionError(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.message = message
        self.status = status


def adjust_balance(employee, delta):
    """Add delta (negative to take days) to the employee's annual leave balance."""
    employee.balance_days += delta


def decide(leave, decision, actor):
    employee = leave.employee
    if actor == employee.name:
        raise DecisionError("you cannot decide your own request", 403)
    if leave.status != "pending":
        raise DecisionError("only pending requests can be decided", 409)

    if decision == "approve":
        if leave.leave_type == "annual":
            if employee.balance_days < leave.days:
                raise DecisionError("not enough annual leave left", 409)
            adjust_balance(employee, -leave.days)
        leave.status = "approved"
    else:
        leave.status = "rejected"

    leave.decided_by = actor
    leave.decided_at = timezone.now()
    leave.save()
    return leave


def cancel(leave, actor):
    employee = leave.employee
    if actor != employee.username:
        raise DecisionError("only the requester can cancel a request", 403)
    if leave.status not in ACTIVE_STATUSES:
        raise DecisionError("only pending or approved requests can be cancelled", 409)

    if leave.leave_type == "annual":
        adjust_balance(employee, leave.days)
    leave.status = "cancelled"
    leave.save()
    return leave
