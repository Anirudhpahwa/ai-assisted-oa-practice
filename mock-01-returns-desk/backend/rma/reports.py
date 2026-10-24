from django.db.models import Count

from .models import STATUSES, ReturnRequest

OPEN_STATUSES = ("requested", "approved", "received")


def build_summary(reason=None):
    returns = ReturnRequest.objects.all()
    if reason:
        returns = returns.filter(reason=reason)

    by_status = {status: 0 for status in STATUSES}
    for row in returns.values("status").annotate(n=Count("id")):
        by_status[row["status"]] = row["n"]

    refunded = returns.filter(status="refunded").aggregate(
        total=Count("refund_total_cents")
    )["total"]
    return {
        "by_status": by_status,
        "open_count": sum(by_status[status] for status in OPEN_STATUSES),
        "refunded_total_cents": refunded or 0,
    }
