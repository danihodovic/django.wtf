from watson import search as watson
from watson.views import SearchView as OriginalSearchView

from django_wtf.core.models import Repository
from django_wtf.core.views.index_view import categories_ordered_by_total_repositories


class SearchView(OriginalSearchView):
    paginate_by = 10
    models = (Repository,)

    def get_template_names(self):  # pyright: ignore [reportIncompatibleMethodOverride]
        if self.request.htmx:
            template_name = "core/search_table.html"
        else:
            template_name = "core/search.html"

        return [template_name]

    def get_queryset(self):
        repositories = Repository.valid.all()

        category = self.request.GET.get("category", None)
        if category and category != "All":
            repositories = repositories.filter(categories__name=category)

        search = self.request.GET.get("q", None)
        if search:
            repositories = watson.filter(repositories, search)
        return repositories

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = categories_ordered_by_total_repositories()
        return ctx
