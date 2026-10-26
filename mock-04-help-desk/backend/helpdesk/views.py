import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from . import queries, reports, serializers, tickets, validators
from .models import Ticket


def get_actor(request):
    return request.headers.get("X-Agent", "system")


def parse_body(request):
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        raise validators.ValidationFailed("request body must be valid JSON")
    if not isinstance(data, dict):
        raise validators.ValidationFailed("request body must be a JSON object")
    return data


def error(message, status=400):
    return JsonResponse({"error": message}, status=status)


def find_ticket(ticket_id):
    return Ticket.objects.filter(pk=ticket_id).first()


@require_http_methods(["GET", "POST"])
def ticket_collection(request):
    if request.method == "GET":
        return list_tickets(request)

    try:
        cleaned = validators.clean_new_ticket(parse_body(request))
    except validators.ValidationFailed as exc:
        return error(exc.message)

    key = (request.headers.get("X-Idempotency-Key") or "").strip() or None
    if key:
        existing = Ticket.objects.filter(idempotency_key=key).first()
        if existing:
            return JsonResponse(serializers.ticket_to_dict(existing))

    ticket = tickets.create_ticket(cleaned, get_actor(request), key)
    return JsonResponse(serializers.ticket_to_dict(ticket), status=201)


def list_tickets(request):
    try:
        params = validators.parse_list_params(request.GET)
    except validators.ValidationFailed as exc:
        return error(exc.message)

    items, total, pages = queries.list_page(params)
    return JsonResponse(
        {
            "total": total,
            "page": params["page"],
            "per_page": params["per_page"],
            "pages": pages,
            "results": [serializers.ticket_to_dict(ticket) for ticket in items],
        }
    )


@require_http_methods(["GET", "PATCH"])
def ticket_item(request, ticket_id):
    ticket = find_ticket(ticket_id)
    if ticket is None:
        return error("ticket not found", 404)
    if request.method == "GET":
        return JsonResponse(serializers.ticket_detail_to_dict(ticket))

    try:
        changes = validators.clean_ticket_update(parse_body(request))
        tickets.update_ticket(ticket, changes, get_actor(request))
    except validators.ValidationFailed as exc:
        return error(exc.message)
    except tickets.TicketError as exc:
        return error(exc.message, exc.status)
    return JsonResponse(serializers.ticket_to_dict(ticket))


@require_http_methods(["POST"])
def change_status(request, ticket_id):
    ticket = find_ticket(ticket_id)
    if ticket is None:
        return error("ticket not found", 404)
    try:
        target = validators.parse_status(parse_body(request))
        tickets.change_status(ticket, target, get_actor(request))
    except validators.ValidationFailed as exc:
        return error(exc.message)
    except tickets.TicketError as exc:
        return error(exc.message, exc.status)
    return JsonResponse(serializers.ticket_to_dict(ticket))


@require_http_methods(["POST"])
def add_comment(request, ticket_id):
    ticket = find_ticket(ticket_id)
    if ticket is None:
        return error("ticket not found", 404)
    try:
        body, internal = validators.parse_comment(parse_body(request))
        comment = tickets.add_comment(ticket, get_actor(request), body, internal)
    except validators.ValidationFailed as exc:
        return error(exc.message)
    except tickets.TicketError as exc:
        return error(exc.message, exc.status)
    return JsonResponse(serializers.comment_to_dict(comment), status=201)


@require_http_methods(["GET"])
def report(request):
    try:
        start, end = validators.parse_range(request.GET)
    except validators.ValidationFailed as exc:
        return error(exc.message)
    return JsonResponse(
        {"from": start.isoformat(), "to": end.isoformat(), "priorities": reports.sla_report(start, end)}
    )
