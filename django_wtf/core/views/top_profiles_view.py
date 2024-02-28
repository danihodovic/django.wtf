from django.views.generic import ListView
from meta.views import MetadataMixin

from django_wtf.core.queries import most_followed_profiles


class TopProfilesView(MetadataMixin, ListView):
    template_name = "core/top_profiles.html"
    paginate_by = 25
    title = "Top contributors to Django projects"
    description = "Listing the top contributors to Django projects"

    def get_queryset(self):
        return most_followed_profiles()
