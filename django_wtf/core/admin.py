# pylint: disable=too-few-public-methods
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from watson.admin import SearchAdmin

from .filters import HasReadmeListFilter
from .models import (
    Category,
    EmailSubscriber,
    Profile,
    ProfileFollowers,
    PypiProject,
    Repository,
    RepositoryStars,
    SocialNews,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "emoji")
    search_fields = ("name",)


@admin.register(Repository)
class RepositoryAdmin(SearchAdmin):
    # class RepositoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "stars",
        "topics",
        "type",
        "created",
        "modified",
    )
    list_filter = ("type", HasReadmeListFilter)
    search_fields = (
        "full_name",
        "topics",
        "description",
        "categories__name",
        "readme_html",
    )
    autocomplete_fields = ("categories",)
    save_on_top = True

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields if f != "categories"]


@admin.register(RepositoryStars)
class RepositoryStarsAdmin(admin.ModelAdmin):
    list_display = ("repository", "created_at", "stars")
    list_filter = ()
    search_fields = ("repository__full_name",)
    date_hierarchy = "created_at"
    advanced_filter_fields = "__all__"

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]


@admin.register(Profile)
class ProfileAdmin(SearchAdmin):
    # class ProfileAdmin(admin.ModelAdmin):
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
class ProfileFollowersAdmin(admin.ModelAdmin):
    list_display = ("profile", "created_at", "followers")
    list_filter = ()
    search_fields = ("profile__login",)
    date_hierarchy = "created_at"


@admin.register(SocialNews)
# class SocialNewsAdmin(SearchAdmin):
class SocialNewsAdmin(admin.ModelAdmin):
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


@admin.register(EmailSubscriber)
class EmailSubscriberAdmin(admin.ModelAdmin):
    list_display = ("user", "created", "modified")
    readonly_fields = ("user", "created", "modified")
    list_filter = ("created",)


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    date_hierarchy = "action_time"
    list_display = (
        "action_time",
        "user",
        "content_type",
        "object_repr",
        "action_flag",
    )
    list_filter = ("action_flag", "content_type", "user")
    search_fields = ("object_repr", "change_message", "user__username")
    readonly_fields = [field.name for field in LogEntry._meta.fields]
    ordering = ("-action_time",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
