from django.contrib.admin.apps import AdminConfig


class CustomAdminConfig(AdminConfig):
    default_site = "django_wtf.customadmin.admin.CustomAdminSite"
