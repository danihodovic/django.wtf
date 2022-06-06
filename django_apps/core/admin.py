# pylint: disable=too-few-public-methods
from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .filters import HasReadmeListFilter
from .models import (
    Category,
    Profile,
    ProfileFollowers,
    PypiProject,
    Repository,
    RepositoryStars,
    SocialNews,
)


@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin):
    list_display = ("id", "name", "emoji")
    search_fields = ("name",)


@admin.register(Repository)
class RepositoryAdmin(ImportExportModelAdmin):
    list_display = (
        "id",
        "full_name",
        "stars",
        "topics",
        "type",
        "created",
    )
    list_filter = ("type", HasReadmeListFilter)
    search_fields = ("name", "topics", "description", "categories__name", "readme_html")
    autocomplete_fields = ("categories",)

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields if f != "categories"]


@admin.register(RepositoryStars)
class RepositoryStarsAdmin(ImportExportModelAdmin):
    list_display = ("repository", "created_at", "stars")
    list_filter = ()
    search_fields = ("repository__full_name",)
    date_hierarchy = "created_at"
    advanced_filter_fields = "__all__"

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]


@admin.register(Profile)
class ProfileAdmin(ImportExportModelAdmin):
    list_display = (
        "login",
        "type",
        "followers",
        "created",
    )
    list_filter = ("type",)
    search_fields = ("login",)

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]


@admin.register(ProfileFollowers)
class ProfileFollowersAdmin(ImportExportModelAdmin):
    list_display = ("profile", "created_at", "followers")
    list_filter = ()
    search_fields = ("profile__login",)
    date_hierarchy = "created_at"


@admin.register(SocialNews)
class SocialNewsAdmin(ImportExportModelAdmin):
    list_display = ("title", "upvotes", "type")
    list_filter = ("type",)
    search_fields = ("title",)
    ordering = ("-upvotes",)

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]


@admin.register(PypiProject)
class PypiProjectAdmin(admin.ModelAdmin):
    list_display = ("repository", "version")
    list_filter = ()

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]


class ProfileResource(resources.ModelResource):
    class Meta:
        model = Profile
        instance_loader = "import_export.instance_loaders.CachedInstanceLoader"
        skip_diff = True
        use_bulk = True


class CategoryResource(resources.ModelResource):
    class Meta:
        model = Category
        instance_loader = "import_export.instance_loaders.CachedInstanceLoader"
        skip_diff = True
        use_bulk = True


class RepositoryResource(resources.ModelResource):
    class Meta:
        model = Repository
        instance_loader = "import_export.instance_loaders.CachedInstanceLoader"
        skip_diff = True
        use_bulk = True


class RepositoryStarsResource(resources.ModelResource):
    class Meta:
        model = RepositoryStars
        instance_loader = "import_export.instance_loaders.CachedInstanceLoader"
        skip_diff = True
        use_bulk = True

    def get_queryset(self):
        return super().get_queryset().select_related("repository")


class SocialNewsResource(resources.ModelResource):
    class Meta:
        model = SocialNews
        instance_loader = "import_export.instance_loaders.CachedInstanceLoader"
        skip_diff = True
        use_bulk = True
