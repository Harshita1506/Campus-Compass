from django import forms

from core.forms import BootstrapFormMixin


class MessageForm(BootstrapFormMixin, forms.Form):
    body = forms.CharField(max_length=2000, widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Write a message…"}))

    def clean_body(self):
        body = self.cleaned_data["body"].strip()
        if not body:
            raise forms.ValidationError("Message cannot be empty.")
        return body
