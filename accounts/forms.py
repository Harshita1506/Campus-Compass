from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from core.forms import BootstrapFormMixin

from .models import Profile

User = get_user_model()


class RegistrationForm(BootstrapFormMixin, UserCreationForm):
    first_name = forms.CharField(max_length=60)
    last_name = forms.CharField(max_length=60)
    email = forms.EmailField(help_text="We'll send a 6-digit verification code to this address.")
    branch = forms.ChoiceField(choices=Profile.Branch.choices)
    academic_year = forms.TypedChoiceField(choices=Profile.Year.choices, coerce=int)
    role = forms.ChoiceField(
        choices=[(User.Role.STUDENT, "Current student"), (User.Role.SENIOR, "Senior / Alumni (mentor)")],
        initial=User.Role.STUDENT,
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email", "role", "branch", "academic_year")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        domain = settings.ALLOWED_EMAIL_DOMAIN
        if domain and not email.endswith("@" + domain):
            raise forms.ValidationError(f"Please use your college email (@{domain}).")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()
            profile = user.profile
            profile.branch = self.cleaned_data["branch"]
            profile.academic_year = self.cleaned_data["academic_year"]
            profile.save()
        return user


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    username = forms.CharField(label="Username or email", widget=forms.TextInput(attrs={"autofocus": True}))


class OTPForm(BootstrapFormMixin, forms.Form):
    code = forms.CharField(
        max_length=6, min_length=6,
        widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "one-time-code",
                                      "placeholder": "6-digit code", "pattern": "[0-9]{6}"}),
    )

    def clean_code(self):
        code = self.cleaned_data["code"].strip()
        if not code.isdigit():
            raise forms.ValidationError("The code contains digits only.")
        return code


class UserUpdateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name")


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("branch", "academic_year", "phone", "linkedin_url", "bio", "avatar")
        widgets = {"bio": forms.Textarea(attrs={"rows": 4})}
        help_texts = {"linkedin_url": "Must be an https://linkedin.com/... link"}

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if phone and not phone.replace("+", "").replace(" ", "").isdigit():
            raise forms.ValidationError("Enter a valid phone number.")
        return phone
