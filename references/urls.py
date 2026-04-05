"""URL routing for References app."""

from django.urls import path

from . import views

app_name = "references"

urlpatterns = [
    # Главная
    path("", views.references_index, name="index"),

    # Клиенты
    path("clients/", views.ClientListView.as_view(), name="client_list"),
    path("clients/create/", views.ClientCreateView.as_view(), name="client_create"),
    path("clients/<int:pk>/", views.ClientDetailView.as_view(), name="client_detail"),
    path("clients/<int:pk>/edit/", views.ClientUpdateView.as_view(), name="client_update"),
    path("clients/<int:pk>/delete/", views.ClientDeleteView.as_view(), name="client_delete"),

    # Типы грузов
    path("cargo-types/", views.CargoTypeListView.as_view(), name="cargotype_list"),
    path("cargo-types/create/", views.CargoTypeCreateView.as_view(), name="cargotype_create"),
    path("cargo-types/<int:pk>/edit/", views.CargoTypeUpdateView.as_view(), name="cargotype_update"),
    path(
        "cargo-types/<int:pk>/delete/",
        views.CargoTypeDeleteView.as_view(),
        name="cargotype_delete",
    ),

    # Нормативы топлива
    path("fuel-norms/", views.FuelNormListView.as_view(), name="fuelnorm_list"),
    path("fuel-norms/create/", views.FuelNormCreateView.as_view(), name="fuelnorm_create"),
    path("fuel-norms/<int:pk>/edit/", views.FuelNormUpdateView.as_view(), name="fuelnorm_update"),
    path(
        "fuel-norms/<int:pk>/delete/",
        views.FuelNormDeleteView.as_view(),
        name="fuelnorm_delete",
    ),
]
