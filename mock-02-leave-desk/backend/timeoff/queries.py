import math

from django.db.models import Count, Q, Sum

from .models import ACTIVE_STATUSES, LeaveRequest


def filter_requests(params):
    leaves = LeaveRequest.objects.select_related("employee")
    if params["employee_id"] is not None:
        leaves = leaves.filter(employee_id=params["employee_id"])
    if params["status"]:
        leaves = leaves.filter(status=params["status"])
    if params["leave_type"]:
        leaves = leaves.filter(leave_type=params["leave_type"])
    if params["department"]:
        leaves = LeaveRequest.objects.filter(employee__department=params["department"])
    return leaves.order_by("start_date", "id")


def list_page(params):
    leaves = filter_requests(params)
    total = leaves.count()
    pages = math.ceil(total / params["per_page"])
    offset = (params["page"] - 1) * params["per_page"]
    items = list(leaves[offset:offset + params["per_page"]])
    return items, total, pages


def who_is_out(day):
    return (
        LeaveRequest.objects.filter(
            status__in=ACTIVE_STATUSES, start_date__lte=day, end_date__gte=day
        )
        .select_related("employee")
        .order_by("employee__name", "id")
    )


def department_summary(year):
    rows = (
        LeaveRequest.objects.filter(start_date__year=year)
        .values("employee__department")
        .annotate(
            approved_days=Sum("days", filter=Q(status="approved")),
            people_out=Count("employee", filter=Q(status="approved")),
            pending=Count("id", filter=Q(status="pending")),
            approved=Count("id", filter=Q(status="approved")),
            rejected=Count("id", filter=Q(status="rejected")),
            cancelled=Count("id", filter=Q(status="cancelled")),
        )
        .order_by("employee__department")
    )
    return [
        {
            "department": row["employee__department"],
            "approved_days": row["approved_days"] or 0,
            "people_out": row["people_out"],
            "requests": {
                "pending": row["pending"],
                "approved": row["approved"],
                "rejected": row["rejected"],
                "cancelled": row["cancelled"],
            },
        }
        for row in rows
    ]
