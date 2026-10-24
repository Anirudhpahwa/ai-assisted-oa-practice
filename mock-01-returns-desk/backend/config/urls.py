from django.urls import include, path

urlpatterns = [
    path("api/", include("rma.urls")),
]
