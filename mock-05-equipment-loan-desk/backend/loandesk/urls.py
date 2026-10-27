from django.urls import path

from . import views

urlpatterns = [
    path("loans/", views.loan_collection),
    path("loans/<int:loan_id>/", views.loan_item),
    path("loans/<int:loan_id>/return/", views.return_loan),
    path("loans/<int:loan_id>/extend/", views.extend_loan),
    path("loans/<int:loan_id>/cancel/", views.cancel_loan),
    path("summary/", views.summary),
]
