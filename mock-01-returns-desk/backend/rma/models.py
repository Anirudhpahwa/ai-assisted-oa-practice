from django.db import models

STATUSES = ["requested", "approved", "received", "refunded", "rejected", "cancelled"]
REASONS = ["damaged", "wrong_item", "not_needed", "other"]


class ReturnRequest(models.Model):
    customer = models.CharField(max_length=120)
    order_number = models.CharField(max_length=40)
    reason = models.CharField(max_length=20, default="not_needed")
    note = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, default="requested")
    refund_total_cents = models.PositiveIntegerField(default=0)
    created_by = models.CharField(max_length=60, default="system")
    decided_by = models.CharField(max_length=60, blank=True, default="")
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ReturnItem(models.Model):
    ret = models.ForeignKey(ReturnRequest, on_delete=models.CASCADE, related_name="items")
    sku = models.CharField(max_length=40)
    quantity = models.PositiveSmallIntegerField()
    unit_price_cents = models.PositiveIntegerField()


class StatusEvent(models.Model):
    ret = models.ForeignKey(ReturnRequest, on_delete=models.CASCADE, related_name="history")
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    actor = models.CharField(max_length=60)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
