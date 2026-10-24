from django.urls import path

from . import views

urlpatterns = [
    path("returns/", views.returns_collection),
    path("returns/summary/", views.summary),
    path("returns/<int:return_id>/", views.return_detail),
    path("returns/<int:return_id>/items/", views.add_item),
    path("returns/<int:return_id>/transition/", views.transition),
]
