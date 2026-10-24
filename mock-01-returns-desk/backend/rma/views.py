import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from . import queries, refunds, reports, serializers, validators, workflow
from .models import ReturnItem, ReturnRequest


def get_agent(request):
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


@require_http_methods(["GET", "POST"])
def returns_collection(request):
    if request.method == "GET":
        return list_returns(request)

    try:
        cleaned = validators.clean_new_return(parse_body(request))
    except validators.ValidationFailed as exc:
        return error(exc.message)

    ret = ReturnRequest.objects.create(created_by=get_agent(request), **cleaned)
    return JsonResponse(serializers.return_to_dict(ret), status=201)


def list_returns(request):
    try:
        params = validators.parse_list_params(request.GET)
    except validators.ValidationFailed as exc:
        return error(exc.message)

    items, total, has_more = queries.list_page(params)
    return JsonResponse(
        {
            "total": total,
            "limit": params["limit"],
            "offset": params["offset"],
            "has_more": has_more,
            "results": [serializers.return_to_dict(ret) for ret in items],
        }
    )


@require_http_methods(["GET"])
def return_detail(request, return_id):
    ret = ReturnRequest.objects.filter(pk=return_id).first()
    if ret is None:
        return error("return not found", 404)
    return JsonResponse(serializers.return_detail(ret))


@require_http_methods(["POST"])
def add_item(request, return_id):
    ret = ReturnRequest.objects.filter(pk=return_id).first()
    if ret is None:
        return error("return not found", 404)

    try:
        cleaned = validators.clean_item(parse_body(request))
    except validators.ValidationFailed as exc:
        return error(exc.message)
    if ret.status != "requested":
        return error("items can only be added while the return is requested", 409)

    item = ReturnItem.objects.create(ret=ret, **cleaned)
    refunds.refresh_refund_total(ret)
    return JsonResponse(serializers.item_to_dict(item), status=201)


@require_http_methods(["POST"])
def transition(request, return_id):
    ret = ReturnRequest.objects.filter(pk=return_id).first()
    if ret is None:
        return error("return not found", 404)

    try:
        target = validators.parse_target_status(parse_body(request))
    except validators.ValidationFailed as exc:
        return error(exc.message)

    try:
        workflow.apply_transition(ret, target, get_agent(request))
    except workflow.TransitionError as exc:
        return error(exc.message, 409)
    return JsonResponse(serializers.return_to_dict(ret))


@require_http_methods(["GET"])
def summary(request):
    try:
        reason = validators.parse_reason_filter(request.GET.get("reason"))
    except validators.ValidationFailed as exc:
        return error(exc.message)
    return JsonResponse(reports.build_summary(reason))
