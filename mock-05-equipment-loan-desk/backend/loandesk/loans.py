from datetime import timedelta

from django.db.models import Sum

from . import fees, schedule
from .models import Equipment, Loan, LoanLine

MAX_EXTENSIONS = 2


class LoanError(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.message = message
        self.status = status


def available_units(equipment):
    """Units not currently out on an active loan."""
    out = (
        LoanLine.objects.filter(equipment=equipment)
        .exclude(loan__status="returned")
        .aggregate(total=Sum("quantity"))["total"]
        or 0
    )
    return equipment.units - out


def _load_equipment(items):
    wanted = []
    for entry in items:
        equipment = Equipment.objects.filter(pk=entry["equipment_id"]).first()
        if equipment is None:
            raise LoanError(f"equipment {entry['equipment_id']} not found", 404)
        wanted.append((equipment, entry["quantity"]))
    return wanted


def create_loan(cleaned, actor):
    wanted = _load_equipment(cleaned["items"])
    categories = {equipment.category for equipment, _ in wanted}
    loan = Loan.objects.create(
        borrower=cleaned["borrower"],
        checked_out_on=cleaned["start"],
        due_on=schedule.due_date(cleaned["start"], categories),
        created_by=actor,
    )
    for equipment, quantity in wanted:
        if quantity > available_units(equipment):
            raise LoanError(f"not enough {equipment.name} available", 409)
        LoanLine.objects.create(loan=loan, equipment=equipment, quantity=quantity)
    return loan


def return_loan(loan, returned_on):
    if returned_on < loan.checked_out_on:
        raise LoanError("returned_on must not be before the checkout date", 400)
    if loan.status != "active":
        raise LoanError("loan is not active", 409)
    lines = list(loan.lines.select_related("equipment"))
    loan.fee_cents = fees.late_fee(lines, loan.checked_out_on, returned_on)
    loan.returned_on = returned_on
    loan.status = "returned"
    loan.save()
    return loan


def extend_loan(loan, days):
    if loan.status != "active":
        raise LoanError("loan is not active", 409)
    if loan.extensions >= MAX_EXTENSIONS:
        raise LoanError("loan cannot be extended again", 409)
    loan.due_on = loan.due_on + timedelta(days=days)
    loan.extensions += 1
    loan.save()
    return loan


def cancel_loan(loan):
    if loan.status != "active":
        raise LoanError("loan is not active", 409)
    loan.status = "cancelled"
    loan.save()
    return loan
