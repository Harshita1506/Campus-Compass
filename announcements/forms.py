from django import forms

from core.forms import BootstrapFormMixin

from .models import Announcement


class AnnouncementForm(BootstrapFormMixin, forms.ModelForm):
    notify_students = forms.BooleanField(required=False, initial=False,
                                         help_text="Send an in-app notification to all verified students")

    class Meta:
        model = Announcement
        fields = ("title", "category", "body", "event_date", "venue", "registration_link", "is_pinned", "is_published")
        widgets = {"body": forms.Textarea(attrs={"rows": 6}),
                   "event_date": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["event_date"].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d"]
