from admin_site_search.views import AdminSiteSearchView
from django_admin_shellx_custom_admin.admin import (
    CustomAdminSite as ShellXCustomAdminSite,
)


class CustomAdminSite(AdminSiteSearchView, ShellXCustomAdminSite):
    pass
