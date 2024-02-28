from django.views.generic import ListView
from meta.views import MetadataMixin

from django_wtf.core.models import SocialNews
from django_wtf.core.queries import one_week_ago


class SocialMediaNewsView(MetadataMixin, ListView):
    paginate_by = 25
    title = "Django News"
    description = "Django social media news"
    template_name = "core/social_media_news.html"

    def get_queryset(self):
        return SocialNews.objects.filter(created_at__gt=one_week_ago).order_by(
            "-upvotes"
        )
