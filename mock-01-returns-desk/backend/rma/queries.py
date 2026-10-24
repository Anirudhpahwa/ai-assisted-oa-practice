from django.db.models import Q

from .models import ReturnRequest

ORDERINGS = {
    "newest": ("-id",),
    "oldest": ("id",),
    "refund_desc": ("refund_total_cents", "id"),
}


def filter_returns(params):
    returns = ReturnRequest.objects.exclude(status="cancelled")
    if params["status"]:
        returns = returns.filter(status=params["status"])
    if params["reason"]:
        returns = returns.filter(reason=params["reason"])
    if params["q"]:
        term = params["q"]
        returns = returns.filter(
            Q(customer__icontains=term)
            & Q(order_number__icontains=term)
            & Q(note__icontains=term)
        )
    return returns


def list_page(params):
    returns = filter_returns(params).order_by(*ORDERINGS[params["sort"]])
    total = returns.count()
    offset, limit = params["offset"], params["limit"]
    items = list(returns[offset:offset + limit])
    has_more = offset + len(items) < total
    return items, total, has_more
