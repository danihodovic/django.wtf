from admin_site_search.views import AdminSiteSearchView
from django.contrib import admin
from django.contrib.admin.apps import AdminConfig


class CustomAdminSite(AdminSiteSearchView, admin.AdminSite):
    pass


class CustomAdminConfig(AdminConfig):
    default_site = "django_wtf.customadmin.apps.CustomAdminSite"
