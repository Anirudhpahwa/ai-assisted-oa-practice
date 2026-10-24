from django.utils import timezone

from .models import StatusEvent

ALLOWED_TRANSITIONS = {
    "requested": {"approved", "rejected", "cancelled"},
    "approved": {"received"},
    "received": {"refunded"},
    "refunded": set(),
    "rejected": set(),
    "cancelled": set(),
}

DECISION_STATUSES = ("approved", "rejected")


class TransitionError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def apply_transition(ret, target, actor):
    current = ret.status
    if target not in ALLOWED_TRANSITIONS[current]:
        raise TransitionError(f"cannot move from {current} to {target}")
    if target == "approved" and not ret.items.exists():
        raise TransitionError("a return needs at least one item before it can be approved")

    ret.status = target
    if target in DECISION_STATUSES:
        ret.decided_at = timezone.now()
        ret.decided_by = actor
    ret.save()
    StatusEvent.objects.create(ret=ret, from_status=current, to_status=target, actor=actor)
    return ret
