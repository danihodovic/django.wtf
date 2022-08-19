from watson import search as watson
from watson.views import SearchView as OriginalSearchView

from django_apps.core.models import Repository


class SearchView(OriginalSearchView):
    template_name = "core/search.html"
    paginate_by = 20
    models = (Repository,)

    def get_queryset(self):
        repositories = Repository.valid.all()
        return watson.filter(repositories, self.query)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx
