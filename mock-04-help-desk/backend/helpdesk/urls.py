from django.urls import path

from . import views

urlpatterns = [
    path("tickets/", views.ticket_collection),
    path("tickets/<int:ticket_id>/", views.ticket_item),
    path("tickets/<int:ticket_id>/status/", views.change_status),
    path("tickets/<int:ticket_id>/comments/", views.add_comment),
    path("report/", views.report),
]
