from django.db import transaction
from django.utils import timezone

from . import sla, workflow
from .models import Comment, HistoryEvent, Ticket


class TicketError(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.message = message
        self.status = status


def record_event(ticket, kind, old, new, actor):
    HistoryEvent.objects.create(ticket=ticket, kind=kind, from_value=old, to_value=new, actor=actor)


def create_ticket(cleaned, actor, key=None):
    created_at = timezone.now()
    return Ticket.objects.create(
        created_by=actor,
        created_at=created_at,
        due_at=sla.due_at_for(created_at, cleaned["priority"]),
        idempotency_key=key,
        **cleaned,
    )


def update_ticket(ticket, changes, actor):
    if ticket.status == "closed":
        raise TicketError("closed tickets cannot be edited", 409)
    with transaction.atomic():
        for kind in ("priority", "assignee"):
            if kind in changes:
                record_event(ticket, kind, getattr(ticket, kind), changes[kind], actor)
        for field, value in changes.items():
            setattr(ticket, field, value)
        if "priority" in changes:
            ticket.due_at = sla.due_at_for(ticket.created_at, ticket.priority)
        ticket.save()


def change_status(ticket, target, actor):
    if not workflow.can_move(ticket.status, target):
        raise TicketError(f"cannot move a {ticket.status} ticket to {target}", 409)
    if target == "resolved" and not ticket.assignee:
        raise TicketError("assign the ticket before resolving it", 409)
    with transaction.atomic():
        record_event(ticket, "status", ticket.status, target, actor)
        if target == "resolved":
            ticket.resolved_at = timezone.now()
        ticket.status = target
        ticket.save()


def add_comment(ticket, author, body, internal):
    if ticket.status == "closed":
        raise TicketError("closed tickets cannot be commented on", 409)
    with transaction.atomic():
        comment = Comment.objects.create(ticket=ticket, author=author, body=body, internal=internal)
        if ticket.status == "waiting" and not internal and author == ticket.requester:
            record_event(ticket, "status", "waiting", "in_progress", author)
            ticket.status = "in_progress"
            ticket.save()
    return comment
