from django.db import transaction
from django.utils import timezone

from . import workflow
from .conflicts import is_live


def submit(session, actor):
    workflow.require_counter(session, actor)
    workflow.move(session, "submitted")
    if not session.lines.exists():
        raise workflow.WorkflowError("nothing has been counted yet", 409)
    session.status = "submitted"
    session.submitted_at = timezone.now()
    session.save(update_fields=["status", "submitted_at"])


def approve(session, actor):
    workflow.forbid_counter(session, actor)
    workflow.move(session, "approved")
    with transaction.atomic():
        for line in session.lines.select_related("product"):
            product = line.product
            product.on_hand += line.variance
            product.save(update_fields=["on_hand"])
        session.status = "approved"
        session.approved_by = actor
        session.approved_at = timezone.now()
        session.save(update_fields=["status", "approved_by", "approved_at"])


def void(session):
    if not is_live(session):
        raise workflow.WorkflowError(f"a {session.status} session cannot be voided", 409)
    workflow.move(session, "voided")
    session.status = "voided"
    session.save(update_fields=["status"])
