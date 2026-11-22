from django import forms
from django.utils import timezone

from core.forms import BootstrapFormMixin

from .models import Item


class ItemForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Item
        fields = ("item_type", "title", "category", "description", "location", "date", "image")
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "item_type": forms.RadioSelect,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["item_type"].widget.attrs["class"] = "form-check-input"

    def clean_date(self):
        date = self.cleaned_data["date"]
        if date > timezone.localdate():
            raise forms.ValidationError("Date cannot be in the future.")
        return date


class ItemFilterForm(forms.Form):
    q = forms.CharField(required=False)
    item_type = forms.ChoiceField(required=False, choices=[("", "Lost & Found")] + list(Item.ItemType.choices))
    category = forms.ChoiceField(required=False, choices=[("", "All categories")] + list(Item.Category.choices))
    status = forms.ChoiceField(required=False, choices=[("", "Any status")] + list(Item.Status.choices))
