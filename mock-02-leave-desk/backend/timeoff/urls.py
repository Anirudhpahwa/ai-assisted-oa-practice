from django.urls import path

from . import views

urlpatterns = [
    path("employees/<int:employee_id>/", views.employee_detail),
    path("leave/", views.leave_collection),
    path("leave/out/", views.who_is_out),
    path("leave/summary/", views.summary),
    path("leave/<int:leave_id>/decision/", views.decide),
    path("leave/<int:leave_id>/cancel/", views.cancel),
]
