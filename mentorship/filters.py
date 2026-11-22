import django_filters
from django.db.models import Q

from .models import SeniorProfile


class SeniorFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    skill = django_filters.CharFilter(field_name="skills__name", lookup_expr="icontains", label="Skill")
    domain = django_filters.ChoiceFilter(choices=SeniorProfile.Domain.choices, empty_label="All domains")
    graduation_year = django_filters.NumberFilter(label="Graduation year")

    class Meta:
        model = SeniorProfile
        fields = ["domain", "graduation_year"]

    def search(self, queryset, name, value):
        return queryset.filter(Q(user__first_name__icontains=value) | Q(user__last_name__icontains=value) |
                               Q(current_company__icontains=value) | Q(designation__icontains=value) |
                               Q(skills__name__icontains=value) | Q(mentorship_interests__icontains=value)).distinct()
