from django.utils.encoding import force_str
from watson.search import SearchAdapter


class RepositorySearchAdapter(SearchAdapter):
    def get_title(self, obj):
        categories = " ".join([c.name for c in obj.categories.all()])
        topics = " ".join(obj.topics)
        return force_str(f"{categories} {topics}")

    def get_description(self, obj):
        return force_str(f"{obj.full_name} {obj.description}")

    def get_content(self, obj):
        return self.prepare_content(force_str(obj.readme_html))
