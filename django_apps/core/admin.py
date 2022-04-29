# pylint: disable=too-few-public-methods
from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import Category, Profile, ProfileFollowers, Repository, RepositoryStars


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
    )
    list_filter = ("type",)
    search_fields = ("name", "topics", "categories__name")

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields if f != "categories"]


@admin.register(RepositoryStars)
class RepositoryStarsAdmin(ImportExportModelAdmin):
    list_display = ("repository", "created_at", "stars")
    list_filter = ()
    date_hierarchy = "created_at"

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]


@admin.register(Profile)
class ProfileAdmin(ImportExportModelAdmin):
    list_display = (
        "login",
        "type",
        "followers",
    )
    list_filter = ("type",)
    search_fields = ("login",)

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]


@admin.register(ProfileFollowers)
class ProfileFollowersAdmin(ImportExportModelAdmin):
    list_display = ("profile", "followers")
    list_filter = ()
    date_hierarchy = "created_at"


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
