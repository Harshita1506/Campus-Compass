from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .models import Building, Room


def _building_json(b):
    return {"id": b.id, "name": b.name, "code": b.code, "type": b.building_type, "type_label": b.get_building_type_display(),
            "lat": float(b.latitude), "lng": float(b.longitude), "floors": b.floors, "description": b.description,
            "hours": b.opening_hours, "is_demo": b.is_demo,
            "departments": [d.name for d in b.departments.all()]}


def _room_json(r):
    return {"id": r.id, "room_number": r.room_number, "name": r.name, "type": r.room_type,
            "type_label": r.get_room_type_display(), "floor": r.floor, "floor_label": r.floor_label,
            "department": r.department.name if r.department else "", "faculty": r.faculty_name,
            "capacity": r.capacity, "description": r.description,
            "building": {"id": r.building_id, "name": r.building.name, "code": r.building.code,
                         "lat": float(r.building.latitude), "lng": float(r.building.longitude)}}


@login_required
def map_view(request):
    return render(request, "locator/map.html", {
        "center_lat": settings.CAMPUS_CENTER_LAT, "center_lng": settings.CAMPUS_CENTER_LNG,
        "zoom": settings.CAMPUS_MAP_ZOOM, "building_types": Building.Type.choices, "room_types": Room.Type.choices,
        "has_demo": Building.objects.filter(is_demo=True).exists(),
    })


@login_required
@require_GET
def api_buildings(request):
    buildings = Building.objects.prefetch_related("departments")
    return JsonResponse({"buildings": [_building_json(b) for b in buildings]})


@login_required
@require_GET
def api_search(request):
    q = request.GET.get("q", "").strip()[:80]
    kind = request.GET.get("type", "").strip()
    rooms = Room.objects.select_related("building", "department")
    buildings = Building.objects.prefetch_related("departments")
    if q:
        rooms = rooms.filter(Q(room_number__icontains=q) | Q(name__icontains=q) | Q(faculty_name__icontains=q) |
                             Q(department__name__icontains=q) | Q(building__name__icontains=q) |
                             Q(building__code__icontains=q) | Q(description__icontains=q))
        buildings = buildings.filter(Q(name__icontains=q) | Q(code__icontains=q) | Q(description__icontains=q) |
                                     Q(departments__name__icontains=q)).distinct()
    if kind:
        if kind in Room.Type.values:
            rooms = rooms.filter(room_type=kind)
        if kind in Building.Type.values:
            buildings = buildings.filter(building_type=kind)
        else:
            buildings = buildings.none()
        if kind not in Room.Type.values:
            rooms = rooms.none()
    if not q and not kind:
        rooms = rooms.none()
    return JsonResponse({"query": q, "buildings": [_building_json(b) for b in buildings[:20]],
                         "rooms": [_room_json(r) for r in rooms[:40]]})
