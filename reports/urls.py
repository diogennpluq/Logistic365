"""URL routing for Reports app."""

from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.reports_index, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("orders/", views.orders_report, name="orders"),
    path("vehicles/", views.vehicles_report, name="vehicles"),
    path("drivers/", views.drivers_report, name="drivers"),
]
