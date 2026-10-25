from django.db.models import Count, F, Q, Sum
from django.db.models.functions import Coalesce

from .models import CountLine


def location_summary(start, end):
    """Shortage report for approved sessions scheduled between start and end."""
    short = Q(variance__lt=0)
    rows = (
        CountLine.objects.filter(
            session__status="approved", session__scheduled_for__range=(start, end)
        )
        .values("session__location")
        .annotate(
            sessions=Count("session", distinct=True),
            lines=Count("id"),
            net_units=Sum("variance"),
            shortage_units=Coalesce(Sum(-F("variance"), filter=short), 0),
            shortage_value_cents=Coalesce(
                Sum(F("variance") * F("product__unit_cost_cents"), filter=short), 0
            ),
        )
    )
    result = [
        {
            "location": row["session__location"],
            "sessions": row["sessions"],
            "lines": row["lines"],
            "net_units": row["net_units"],
            "shortage_units": row["shortage_units"],
            "shortage_value_cents": row["shortage_value_cents"],
        }
        for row in rows
    ]
    result.sort(key=lambda row: (-row["shortage_value_cents"], row["location"]))
    return result
