from django import forms

from core.forms import BootstrapFormMixin

from .models import Enquiry, Product, ProductReport


class ProductForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = ("title", "category", "condition", "price", "description", "image", "image_2", "image_3")
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}
        labels = {"image": "Main photo", "image_2": "Photo 2 (optional)", "image_3": "Photo 3 (optional)",
                  "price": "Price (₹)"}


class EnquiryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ("message", "offered_price")
        widgets = {"message": forms.Textarea(attrs={"rows": 3, "placeholder": "Hi! Is this still available?"})}
        labels = {"offered_price": "Your offer (₹, optional)"}


class ReportForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ProductReport
        fields = ("reason", "details")
        widgets = {"details": forms.Textarea(attrs={"rows": 3})}


class ProductFilterForm(forms.Form):
    SORT_CHOICES = [("newest", "Newest first"), ("price_asc", "Price: low to high"),
                    ("price_desc", "Price: high to low"), ("oldest", "Oldest first")]
    q = forms.CharField(required=False)
    category = forms.ChoiceField(required=False, choices=[("", "All categories")] + list(Product.Category.choices))
    condition = forms.ChoiceField(required=False, choices=[("", "Any condition")] + list(Product.Condition.choices))
    min_price = forms.DecimalField(required=False, min_value=0)
    max_price = forms.DecimalField(required=False, min_value=0)
    sort = forms.ChoiceField(required=False, choices=SORT_CHOICES)
    include_sold = forms.BooleanField(required=False)
