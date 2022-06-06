from django.views.generic.detail import DetailView

from .models import Repository


class RepositoryDetail(DetailView):
    queryset = Repository.valid.filter(readme_html__isnull=False)

    def get_object(self, *args, **kwargs):
        return Repository.objects.get(full_name=self.kwargs.get("full_name"))
