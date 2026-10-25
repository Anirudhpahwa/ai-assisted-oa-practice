from django.db import models

SESSION_STATUSES = ["open", "submitted", "approved", "voided"]
LIVE_STATUSES = ("open", "submitted")


class Product(models.Model):
    sku = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=120)
    on_hand = models.IntegerField(default=0)
    unit_cost_cents = models.IntegerField(default=0)


class CountSession(models.Model):
    location = models.CharField(max_length=80)
    scheduled_for = models.DateField()
    assigned_to = models.CharField(max_length=60)
    status = models.CharField(max_length=20, default="open")
    note = models.TextField(blank=True, default="")
    created_by = models.CharField(max_length=60, default="system")
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.CharField(max_length=60, blank=True, default="")
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CountLine(models.Model):
    session = models.ForeignKey(CountSession, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="count_lines")
    expected = models.IntegerField()
    counted = models.IntegerField()
    variance = models.IntegerField()
    counted_by = models.CharField(max_length=60, default="system")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("session", "product")]
