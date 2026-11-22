import django_filters
from django.db.models import Q
from django.utils import timezone

from .models import Announcement


class AnnouncementFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    category = django_filters.ChoiceFilter(choices=Announcement.Category.choices, empty_label="All categories")
    upcoming = django_filters.BooleanFilter(method="filter_upcoming", label="Upcoming events only",
                                            widget=django_filters.widgets.BooleanWidget())

    class Meta:
        model = Announcement
        fields = ["category"]

    def search(self, queryset, name, value):
        return queryset.filter(Q(title__icontains=value) | Q(body__icontains=value) | Q(venue__icontains=value))

    def filter_upcoming(self, queryset, name, value):
        if value:
            return queryset.filter(event_date__gte=timezone.now()).order_by("event_date")
        return queryset
