from django.db.models import Q

from .models import CountSession

SORTS = {
    "scheduled": ("scheduled_for", "id"),
    "scheduled_desc": ("-scheduled_for", "id"),
    "location": ("location", "id"),
}


def filter_sessions(params):
    sessions = CountSession.objects.all()
    if params["status"]:
        sessions = sessions.filter(status=params["status"])
    else:
        sessions = sessions.exclude(status="voided")
    if params["location"]:
        sessions = sessions.filter(location__iexact=params["location"])
    if params["assigned_to"]:
        sessions = sessions.filter(assigned_to=params["assigned_to"])
    if params["scheduled_from"]:
        sessions = sessions.filter(scheduled_for__gte=params["scheduled_from"])
    if params["scheduled_to"]:
        sessions = sessions.filter(scheduled_for__lt=params["scheduled_to"])
    if params["q"]:
        sessions = sessions.filter(
            Q(location__icontains=params["q"]) | Q(note__icontains=params["q"])
        )
    return sessions


def list_page(params):
    sessions = filter_sessions(params).order_by(*SORTS[params["sort"]])
    total = sessions.count()
    pages = (total + params["per_page"] - 1) // params["per_page"]
    start = (params["page"] - 1) * params["per_page"]
    return list(sessions[start : start + params["per_page"]]), total, pages
