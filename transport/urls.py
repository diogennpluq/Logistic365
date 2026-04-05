from django.urls import path

from . import views

app_name = "transport"

urlpatterns = [
    path("", views.VehicleListView.as_view(), name="list"),
    path("drivers/", views.DriverListView.as_view(), name="drivers"),
]
