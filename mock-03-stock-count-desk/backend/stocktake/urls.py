from django.urls import path

from . import views

urlpatterns = [
    path("sessions/", views.session_collection),
    path("sessions/<int:session_id>/", views.session_detail),
    path("sessions/<int:session_id>/lines/", views.record_line),
    path("sessions/<int:session_id>/submit/", views.submit),
    path("sessions/<int:session_id>/approve/", views.approve),
    path("sessions/<int:session_id>/void/", views.void),
    path("summary/", views.summary),
]
