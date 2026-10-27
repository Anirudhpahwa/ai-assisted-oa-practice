import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from . import loans, queries, reports, serializers, validators
from .models import Loan


def get_actor(request):
    return request.headers.get("X-Clerk", "system")


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


def find_loan(loan_id):
    return Loan.objects.filter(pk=loan_id).first()


@require_http_methods(["GET", "POST"])
def loan_collection(request):
    if request.method == "GET":
        return list_loans(request)

    try:
        cleaned = validators.clean_new_loan(parse_body(request))
        loan = loans.create_loan(cleaned, get_actor(request))
    except validators.ValidationFailed as exc:
        return error(exc.message)
    except loans.LoanError as exc:
        return error(exc.message, exc.status)
    return JsonResponse(serializers.loan_to_dict(loan), status=201)


def list_loans(request):
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
            "results": [serializers.loan_to_dict(loan) for loan in items],
        }
    )


@require_http_methods(["GET"])
def loan_item(request, loan_id):
    loan = find_loan(loan_id)
    if loan is None:
        return error("loan not found", 404)
    return JsonResponse(serializers.loan_to_dict(loan))


@require_http_methods(["POST"])
def return_loan(request, loan_id):
    loan = find_loan(loan_id)
    if loan is None:
        return error("loan not found", 404)
    try:
        returned_on = validators.parse_return(parse_body(request))
        loans.return_loan(loan, returned_on)
    except validators.ValidationFailed as exc:
        return error(exc.message)
    except loans.LoanError as exc:
        return error(exc.message, exc.status)
    return JsonResponse(serializers.loan_to_dict(loan))


@require_http_methods(["POST"])
def extend_loan(request, loan_id):
    loan = find_loan(loan_id)
    if loan is None:
        return error("loan not found", 404)
    try:
        days = validators.parse_extend(parse_body(request))
        loans.extend_loan(loan, days)
    except validators.ValidationFailed as exc:
        return error(exc.message)
    except loans.LoanError as exc:
        return error(exc.message, exc.status)
    return JsonResponse(serializers.loan_to_dict(loan))


@require_http_methods(["POST"])
def cancel_loan(request, loan_id):
    loan = find_loan(loan_id)
    if loan is None:
        return error("loan not found", 404)
    try:
        loans.cancel_loan(loan)
    except loans.LoanError as exc:
        return error(exc.message, exc.status)
    return JsonResponse(serializers.loan_to_dict(loan))


@require_http_methods(["GET"])
def summary(request):
    try:
        start, end = validators.parse_range(request.GET)
    except validators.ValidationFailed as exc:
        return error(exc.message)
    return JsonResponse(
        {"from": start.isoformat(), "to": end.isoformat(), "borrowers": reports.borrower_summary(start, end)}
    )
