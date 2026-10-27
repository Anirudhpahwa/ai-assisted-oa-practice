from django.db.models import Q
from django.db.models.functions import Lower

from .models import Loan

SORTS = {
    "due": ("due_on", "id"),
    "newest": ("-checked_out_on", "id"),
    "borrower": (Lower("borrower"), "due_on", "id"),
}


def filter_loans(params):
    loans = Loan.objects.all()
    if params["statuses"]:
        loans = loans.filter(status__in=params["statuses"])
    if params["borrower"]:
        loans = loans.filter(borrower=params["borrower"])
    if params["equipment_id"] is not None:
        loans = Loan.objects.filter(lines__equipment_id=params["equipment_id"])
    if params["q"]:
        loans = loans.filter(
            Q(borrower__icontains=params["q"]) | Q(lines__equipment__name__icontains=params["q"])
        )
    if params["due_from"]:
        loans = loans.filter(due_on__gte=params["due_from"])
    if params["due_to"]:
        loans = loans.filter(due_on__lte=params["due_to"])
    if params["overdue_on"]:
        loans = loans.filter(status="active", due_on__lt=params["overdue_on"])
    return loans.distinct()


def list_page(params):
    loans = filter_loans(params).order_by(*SORTS[params["sort"]])
    total = loans.count()
    pages = total // params["per_page"]
    start = (params["page"] - 1) * params["per_page"]
    return list(loans[start : start + params["per_page"]]), total, pages
