from django import forms

from core.forms import BootstrapFormMixin

from .models import RoommateProfile, RoommateRequest


class RoommateProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = RoommateProfile
        fields = ("headline", "about", "budget_min", "budget_max", "preferred_location", "accommodation_type",
                  "food_preference", "sleep_schedule", "cleanliness", "move_in_date", "is_active")
        widgets = {"about": forms.Textarea(attrs={"rows": 4}), "move_in_date": forms.DateInput(attrs={"type": "date"})}
        labels = {"budget_min": "Minimum budget (₹/month)", "budget_max": "Maximum budget (₹/month)",
                  "is_active": "Show my profile to others"}


class RoommateRequestForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = RoommateRequest
        fields = ("message",)
        widgets = {"message": forms.Textarea(attrs={"rows": 3, "placeholder": "Introduce yourself…"})}


class RoommateFilterForm(forms.Form):
    q = forms.CharField(required=False)
    location = forms.ChoiceField(required=False, choices=[("", "Any location")] + list(RoommateProfile.Location.choices))
    accommodation = forms.ChoiceField(required=False,
                                      choices=[("", "Any type")] + list(RoommateProfile.Accommodation.choices))
    food = forms.ChoiceField(required=False, choices=[("", "Any food")] + list(RoommateProfile.Food.choices))
    sleep = forms.ChoiceField(required=False, choices=[("", "Any schedule")] + list(RoommateProfile.Sleep.choices))
    max_budget = forms.IntegerField(required=False, min_value=0)
    sort = forms.ChoiceField(required=False, choices=[("match", "Best match"), ("newest", "Newest"),
                                                      ("budget", "Lowest budget")])
