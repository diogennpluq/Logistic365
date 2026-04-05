"""URL routing for Routes app."""

from django.urls import path

from . import views

app_name = "routes"

urlpatterns = [
    path("", views.RouteListView.as_view(), name="list"),
    path("create/", views.RouteCreateView.as_view(), name="create"),
    path("<int:pk>/", views.RouteDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.RouteUpdateView.as_view(), name="edit"),
    path("<int:pk>/calculate/", views.route_calculate, name="calculate"),
    path("<int:pk>/start/", views.route_start, name="start"),
    path("<int:pk>/complete/", views.route_complete, name="complete"),
    path("<int:pk>/cancel/", views.route_cancel, name="cancel"),
    path("<int:pk>/map/", views.route_map, name="map"),
    path("<int:pk>/geocode/", views.route_geocode, name="geocode"),
    path("<int:pk>/add-order/<int:order_id>/", views.route_add_order, name="add_order"),
    path(
        "<int:pk>/remove-order/<int:order_id>/",
        views.route_remove_order,
        name="remove_order",
    ),
]
