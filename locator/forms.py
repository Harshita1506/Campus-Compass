from django import forms

from core.forms import BootstrapFormMixin

from .models import Building, Department, Room


class BuildingForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Building
        fields = ("name", "code", "building_type", "description", "latitude", "longitude", "floors",
                  "opening_hours", "is_demo")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class RoomForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Room
        fields = ("building", "room_number", "name", "room_type", "floor", "department", "faculty_name",
                  "capacity", "description")


class DepartmentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Department
        fields = ("name", "code", "building")
