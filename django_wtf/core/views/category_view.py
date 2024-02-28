from django.core.paginator import Paginator
from django.views.generic import DetailView
from meta.views import MetadataMixin

from django_wtf.core.models import Category, Repository


class CategoryView(MetadataMixin, DetailView):
    model = Category

    def get_object(self, *args, **kwargs):
        return Category.objects.get(name=self.kwargs.get("name"))

    def get_context_data(self, *, _=None, **kwargs):  # pylint: disable=arguments-differ
        context = super().get_context_data()
        repos = self.matching_repositories()
        paginator = Paginator(repos, 25)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        context["paginator"] = paginator
        context["page_obj"] = page_obj
        context["category"] = self.get_object()
        return context

    def get_meta_title(self, context=None):
        return f"django.wtf: projects providing {self.category_name}"

    def get_meta_description(self, context=None):
        repos = self.matching_repositories()
        repo_names = ", ".join([r.full_name for r in repos[0:10]])
        return f"Common apps used for {self.category_name} are: {repo_names}"

    def matching_repositories(self):
        repos = Repository.valid.filter(categories__name=self.category_name).distinct()
        repos = repos.order_by("-stars")
        return repos

    @property
    def category_name(self):
        return self.kwargs.get("name")
