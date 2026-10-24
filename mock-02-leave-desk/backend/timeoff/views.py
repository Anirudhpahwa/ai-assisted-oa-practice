import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from . import conflicts, decisions, queries, serializers, validators
from .models import Employee, LeaveRequest


def get_actor(request):
    return request.headers.get("X-User", "system")


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


@require_http_methods(["GET"])
def employee_detail(request, employee_id):
    employee = Employee.objects.filter(pk=employee_id).first()
    if employee is None:
        return error("employee not found", 404)
    return JsonResponse(serializers.employee_to_dict(employee))


@require_http_methods(["GET", "POST"])
def leave_collection(request):
    if request.method == "GET":
        return list_leave(request)

    try:
        cleaned = validators.clean_new_request(parse_body(request))
    except validators.ValidationFailed as exc:
        return error(exc.message)

    employee = Employee.objects.filter(pk=cleaned.pop("employee_id")).first()
    if employee is None:
        return error("employee not found", 404)
    if conflicts.find_conflict(employee, cleaned["start_date"], cleaned["end_date"]):
        return error("the dates overlap another request", 409)

    leave = LeaveRequest.objects.create(employee=employee, created_by=get_actor(request), **cleaned)
    return JsonResponse(serializers.leave_to_dict(leave), status=201)


def list_leave(request):
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
            "results": [serializers.leave_to_dict(leave) for leave in items],
        }
    )


@require_http_methods(["POST"])
def decide(request, leave_id):
    leave = LeaveRequest.objects.select_related("employee").filter(pk=leave_id).first()
    if leave is None:
        return error("request not found", 404)

    try:
        decision = validators.parse_decision(parse_body(request))
    except validators.ValidationFailed as exc:
        return error(exc.message)

    try:
        decisions.decide(leave, decision, get_actor(request))
    except decisions.DecisionError as exc:
        return error(exc.message, exc.status)
    return JsonResponse(serializers.leave_to_dict(leave))


@require_http_methods(["POST"])
def cancel(request, leave_id):
    leave = LeaveRequest.objects.select_related("employee").filter(pk=leave_id).first()
    if leave is None:
        return error("request not found", 404)

    try:
        decisions.cancel(leave, get_actor(request))
    except decisions.DecisionError as exc:
        return error(exc.message, exc.status)
    return JsonResponse(serializers.leave_to_dict(leave))


@require_http_methods(["GET"])
def who_is_out(request):
    try:
        day = validators.parse_on_date(request.GET)
    except validators.ValidationFailed as exc:
        return error(exc.message)

    leaves = queries.who_is_out(day)
    return JsonResponse(
        {"date": day.isoformat(), "results": [serializers.leave_to_dict(leave) for leave in leaves]}
    )


@require_http_methods(["GET"])
def summary(request):
    try:
        year = validators.parse_year(request.GET)
    except validators.ValidationFailed as exc:
        return error(exc.message)
    return JsonResponse({"year": year, "departments": queries.department_summary(year)})
