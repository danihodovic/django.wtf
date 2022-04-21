from django.contrib import admin

from .models import Profile, ProfileFollowers, Repository, RepositoryStars


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
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
class RepositoryStarsAdmin(admin.ModelAdmin):
    list_display = ("repository", "created_at", "stars")
    list_filter = ()
    date_hierarchy = "created_at"


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "login",
        "type",
    )
    list_filter = ()


@admin.register(ProfileFollowers)
class ProfileFollowersAdmin(admin.ModelAdmin):
    list_display = ("profile", "followers")
    list_filter = ()
    date_hierarchy = "created_at"
