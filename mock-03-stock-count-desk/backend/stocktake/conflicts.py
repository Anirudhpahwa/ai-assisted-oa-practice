from .models import LIVE_STATUSES, CountSession


def find_conflict(location):
    """A location can only have one session in progress at a time."""
    return CountSession.objects.filter(location__iexact=location, status="open").first()


def is_live(session):
    return session.status in LIVE_STATUSES
