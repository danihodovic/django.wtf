from watson import search as watson
from watson.views import SearchView as OriginalSearchView

from django_wtf.core.models import Repository
from django_wtf.core.models.category_model import Category


class SearchView(OriginalSearchView):
    paginate_by = 20
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

    def categories_ordered_by_total_repositories(self):
        categories = []
        for c in Category.objects.all():
            count_matching_repositories = Repository.objects.filter(
                categories__in=[c]
            ).count()
            if count_matching_repositories:
                setattr(c, "total_repositories", count_matching_repositories)
                categories.append(c)
        return sorted(categories, key=lambda c: c.total_repositories, reverse=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = self.categories_ordered_by_total_repositories()
        return ctx
