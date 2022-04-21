from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Profile, ProfileFollowers, Repository, RepositoryStars


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
    search_fields = ("name",)


@admin.register(RepositoryStars)
class RepositoryStarsAdmin(ImportExportModelAdmin):
    list_display = ("repository", "created_at", "stars")
    list_filter = ()
    date_hierarchy = "created_at"


@admin.register(Profile)
class ProfileAdmin(ImportExportModelAdmin):
    list_display = (
        "login",
        "type",
    )
    list_filter = ()


@admin.register(ProfileFollowers)
class ProfileFollowersAdmin(ImportExportModelAdmin):
    list_display = ("profile", "followers")
    list_filter = ()
    date_hierarchy = "created_at"
