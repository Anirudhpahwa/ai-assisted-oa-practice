from django.db.models import Case, IntegerField, Q, Value, When
from django.utils import timezone

from . import dates
from .models import DONE_STATUSES, PRIORITIES, Ticket

PRIORITY_RANK = Case(
    *[When(priority=name, then=Value(rank)) for rank, name in enumerate(reversed(PRIORITIES))],
    output_field=IntegerField(),
)

SORTS = {
    "newest": ("-created_at", "id"),
    "due": ("due_at", "id"),
    "priority": ("rank", "due_at", "id"),
}


def filter_tickets(params):
    tickets = Ticket.objects.all()
    if params["statuses"]:
        tickets = tickets.filter(status__in=params["statuses"])
    if params["priority"]:
        tickets = tickets.filter(priority=params["priority"])
    if params["assignee"] == "none":
        tickets = tickets.filter(assignee__isnull=True)
    elif params["assignee"]:
        tickets = tickets.filter(assignee=params["assignee"])
    if params["requester"]:
        tickets = tickets.filter(requester=params["requester"])
    if params["q"]:
        tickets = tickets.filter(
            Q(title__icontains=params["q"]) | Q(description__icontains=params["q"])
        )
    low, high = dates.day_bounds(params["created_from"], params["created_to"])
    if low:
        tickets = tickets.filter(created_at__gte=low)
    if high:
        tickets = tickets.filter(created_at__lt=high)
    if params["overdue"]:
        tickets = tickets.filter(due_at__lt=timezone.now()).exclude(status__in=DONE_STATUSES)
    return tickets


def list_page(params):
    tickets = filter_tickets(params).annotate(rank=PRIORITY_RANK).order_by(*SORTS[params["sort"]])
    total = tickets.count()
    pages = (total + params["per_page"] - 1) // params["per_page"]
    start = (params["page"] - 1) * params["per_page"]
    return list(tickets[start : start + params["per_page"]]), total, pages
