from django import forms


class BootstrapFormMixin:
    """Apply Bootstrap 5 classes to every widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput,)):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-select")
            elif isinstance(widget, forms.ClearableFileInput) or isinstance(widget, forms.FileInput):
                widget.attrs.setdefault("class", "form-control")
                widget.attrs.setdefault("accept", "image/*")
            else:
                widget.attrs.setdefault("class", "form-control")
            if field.required and not isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("required", "required")
