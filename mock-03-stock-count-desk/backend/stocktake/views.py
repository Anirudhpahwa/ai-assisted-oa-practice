import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from . import approval, conflicts, counts, queries, reports, serializers, validators, workflow
from .models import CountSession, Product


def get_actor(request):
    return request.headers.get("X-Staff", "system")


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


def find_session(session_id):
    return CountSession.objects.filter(pk=session_id).first()


@require_http_methods(["GET", "POST"])
def session_collection(request):
    if request.method == "GET":
        return list_sessions(request)

    try:
        cleaned = validators.clean_new_session(parse_body(request))
    except validators.ValidationFailed as exc:
        return error(exc.message)

    if conflicts.find_conflict(cleaned["location"]):
        return error("this location already has a session in progress", 409)

    actor = get_actor(request)
    assigned_to = cleaned.pop("assigned_to") or actor
    session = CountSession.objects.create(assigned_to=assigned_to, created_by=actor, **cleaned)
    return JsonResponse(serializers.session_to_dict(session), status=201)


def list_sessions(request):
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
            "results": [serializers.session_to_dict(session) for session in items],
        }
    )


@require_http_methods(["GET"])
def session_detail(request, session_id):
    session = find_session(session_id)
    if session is None:
        return error("session not found", 404)
    return JsonResponse(serializers.session_detail_to_dict(session))


@require_http_methods(["POST"])
def record_line(request, session_id):
    session = find_session(session_id)
    if session is None:
        return error("session not found", 404)

    try:
        sku, counted = validators.parse_count(parse_body(request))
    except validators.ValidationFailed as exc:
        return error(exc.message)

    product = Product.objects.filter(sku=sku).first()
    if product is None:
        return error("product not found", 404)

    actor = get_actor(request)
    try:
        workflow.require_counter(session, actor)
        workflow.require_open(session)
    except workflow.WorkflowError as exc:
        return error(exc.message, exc.status)

    line, created = counts.record_count(session, product, counted, actor)
    return JsonResponse(serializers.line_to_dict(line), status=201 if created else 200)


@require_http_methods(["POST"])
def submit(request, session_id):
    session = find_session(session_id)
    if session is None:
        return error("session not found", 404)
    try:
        approval.submit(session, get_actor(request))
    except workflow.WorkflowError as exc:
        return error(exc.message, exc.status)
    return JsonResponse(serializers.session_to_dict(session))


@require_http_methods(["POST"])
def approve(request, session_id):
    session = find_session(session_id)
    if session is None:
        return error("session not found", 404)
    try:
        approval.approve(session, get_actor(request))
    except workflow.WorkflowError as exc:
        return error(exc.message, exc.status)
    return JsonResponse(serializers.session_to_dict(session))


@require_http_methods(["POST"])
def void(request, session_id):
    session = find_session(session_id)
    if session is None:
        return error("session not found", 404)
    try:
        approval.void(session)
    except workflow.WorkflowError as exc:
        return error(exc.message, exc.status)
    return JsonResponse(serializers.session_to_dict(session))


@require_http_methods(["GET"])
def summary(request):
    try:
        start, end = validators.parse_range(request.GET)
    except validators.ValidationFailed as exc:
        return error(exc.message)
    return JsonResponse(
        {
            "from": start.isoformat(),
            "to": end.isoformat(),
            "locations": reports.location_summary(start, end),
        }
    )
