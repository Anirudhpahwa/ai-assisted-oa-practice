from .models import Loan


def borrower_summary(start, end):
    loans = (
        Loan.objects.filter(checked_out_on__gte=start, checked_out_on__lte=end)
        .exclude(status="cancelled")
        .prefetch_related("lines")
    )
    rows = {}
    for loan in loans:
        row = rows.setdefault(
            loan.borrower,
            {"borrower": loan.borrower, "loans": 0, "units": 0, "late_returns": 0, "fees_cents": 0},
        )
        row["loans"] += 1
        row["units"] += sum(line.quantity for line in loan.lines.all())
        if loan.status == "returned" and loan.returned_on > loan.due_on:
            row["late_returns"] += 1
        row["fees_cents"] += loan.fee_cents
    return sorted(rows.values(), key=lambda row: (-row["fees_cents"], row["borrower"]))
