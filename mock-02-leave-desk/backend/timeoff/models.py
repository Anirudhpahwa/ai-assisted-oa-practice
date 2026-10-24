from django.db import models

LEAVE_TYPES = ["annual", "sick", "unpaid"]
STATUSES = ["pending", "approved", "rejected", "cancelled"]
ACTIVE_STATUSES = ("pending", "approved")


class Employee(models.Model):
    name = models.CharField(max_length=120)
    username = models.CharField(max_length=60, unique=True)
    department = models.CharField(max_length=60)
    balance_days = models.IntegerField(default=20)


class LeaveRequest(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="leave_requests")
    leave_type = models.CharField(max_length=20, default="annual")
    start_date = models.DateField()
    end_date = models.DateField()
    days = models.PositiveSmallIntegerField()
    reason = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, default="pending")
    created_by = models.CharField(max_length=60, default="system")
    decided_by = models.CharField(max_length=60, blank=True, default="")
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
