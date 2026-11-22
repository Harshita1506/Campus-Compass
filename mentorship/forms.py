from django import forms

from core.forms import BootstrapFormMixin

from .models import MentorshipRequest, SeniorProfile, Skill


class SeniorProfileForm(BootstrapFormMixin, forms.ModelForm):
    skills_text = forms.CharField(label="Skills", help_text="Comma separated, e.g. Python, Django, System Design",
                                  max_length=400)

    class Meta:
        model = SeniorProfile
        fields = ("branch", "graduation_year", "current_company", "designation", "domain", "introduction",
                  "achievements", "mentorship_interests", "linkedin_url", "github_url", "is_available")
        widgets = {"introduction": forms.Textarea(attrs={"rows": 4}), "achievements": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["skills_text"].initial = ", ".join(self.instance.skills.values_list("name", flat=True))
        order = ["branch", "graduation_year", "current_company", "designation", "domain", "skills_text"]
        self.order_fields(order)

    def clean_skills_text(self):
        names = [s.strip()[:50] for s in self.cleaned_data["skills_text"].split(",") if s.strip()]
        if not names:
            raise forms.ValidationError("Add at least one skill.")
        return list(dict.fromkeys(names))[:15]

    def save_skills(self, profile):
        skills = []
        for name in self.cleaned_data["skills_text"]:
            skill = Skill.objects.filter(name__iexact=name).first() or Skill.objects.create(name=name)
            skills.append(skill)
        profile.skills.set(skills)


class MentorshipRequestForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = MentorshipRequest
        fields = ("topic", "message")
        widgets = {"message": forms.Textarea(attrs={"rows": 4, "placeholder": "What would you like guidance on?"})}


class ResponseForm(BootstrapFormMixin, forms.Form):
    response_note = forms.CharField(required=False, max_length=500, widget=forms.Textarea(attrs={"rows": 2}))
