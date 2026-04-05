"""Tracking views."""

import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from transport.models import Vehicle


@login_required
def tracking_map(request):
    """Карта с активными транспортными средствами (Leaflet)."""
    vehicles = Vehicle.objects.filter(status__in=["on_line", "ok"]).order_by("plate_number")

    vehicle_markers = []
    for v in vehicles:
        latest_event = v.orders.first()
        lat = None
        lng = None
        if latest_event:
            last_tracking = latest_event.tracking_events.first()
            if last_tracking and last_tracking.latitude and last_tracking.longitude:
                lat = float(last_tracking.latitude)
                lng = float(last_tracking.longitude)

        vehicle_markers.append({
            "id": v.pk,
            "plate_number": v.plate_number,
            "vehicle_type": v.get_vehicle_type_display(),
            "brand_model": f"{v.brand} {v.model}".strip(),
            "status": v.status,
            "status_display": v.get_status_display(),
            "lat": lat,
            "lng": lng,
        })

    vehicles_with_coords = [v for v in vehicle_markers if v["lat"] and v["lng"]]
    vehicles_without_coords = [v for v in vehicle_markers if not v["lat"] or not v["lng"]]

    context = {
        "vehicles_json": json.dumps(vehicle_markers),
        "total_vehicles": len(vehicle_markers),
        "vehicles_with_coords": vehicles_with_coords,
        "vehicles_without_coords": vehicles_without_coords,
        "vehicles_with_coords_count": len(vehicles_with_coords),
        "vehicles_without_coords_count": len(vehicles_without_coords),
    }
    return render(request, "tracking/map.html", context)
