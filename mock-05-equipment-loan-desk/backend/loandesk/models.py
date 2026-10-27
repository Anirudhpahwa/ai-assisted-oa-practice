from django.db import models
from django.utils import timezone

CATEGORIES = ["laptop", "camera", "audio", "tools"]
LOAN_STATUSES = ["active", "returned", "cancelled"]


class Equipment(models.Model):
    name = models.CharField(max_length=80, unique=True)
    category = models.CharField(max_length=20)
    units = models.PositiveIntegerField(default=1)
    daily_fee_cents = models.PositiveIntegerField(default=0)


class Loan(models.Model):
    borrower = models.CharField(max_length=60)
    status = models.CharField(max_length=20, default="active")
    checked_out_on = models.DateField()
    due_on = models.DateField()
    returned_on = models.DateField(null=True, blank=True)
    extensions = models.PositiveIntegerField(default=0)
    fee_cents = models.PositiveIntegerField(default=0)
    created_by = models.CharField(max_length=60, default="system")
    created_at = models.DateTimeField(default=timezone.now)


class LoanLine(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="lines")
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name="lines")
    quantity = models.PositiveIntegerField()

    class Meta:
        unique_together = [("loan", "equipment")]
