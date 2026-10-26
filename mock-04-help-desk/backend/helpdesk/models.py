from django.db import models
from django.utils import timezone

PRIORITIES = ["low", "normal", "high", "urgent"]
STATUSES = ["open", "in_progress", "waiting", "resolved", "closed"]
DONE_STATUSES = ("resolved", "closed")


class Ticket(models.Model):
    title = models.CharField(max_length=80)
    description = models.TextField(blank=True, default="")
    requester = models.CharField(max_length=60)
    priority = models.CharField(max_length=20, default="normal")
    status = models.CharField(max_length=20, default="open")
    assignee = models.CharField(max_length=60, blank=True, default="")
    due_at = models.DateTimeField()
    resolved_at = models.DateTimeField(null=True, blank=True)
    idempotency_key = models.CharField(max_length=100, null=True, blank=True, unique=True)
    created_by = models.CharField(max_length=60, default="system")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)


class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    author = models.CharField(max_length=60)
    body = models.TextField()
    internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)


class HistoryEvent(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="history")
    kind = models.CharField(max_length=20)
    from_value = models.CharField(max_length=60, blank=True, default="")
    to_value = models.CharField(max_length=60, blank=True, default="")
    actor = models.CharField(max_length=60)
    created_at = models.DateTimeField(default=timezone.now)
