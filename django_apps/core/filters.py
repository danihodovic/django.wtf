from django.contrib import admin


class HasReadmeListFilter(admin.SimpleListFilter):
    title = "has indexed README"
    parameter_name = "has_readme"

    def lookups(self, request, model_admin):
        return (
            ("true", "yes"),
            ("false", "no"),
        )

    def queryset(self, request, queryset):
        if self.value() == "true":
            return queryset.filter(readme_html__isnull=False)
        if self.value() == "false":
            return queryset.filter(readme_html__isnull=True)
        return queryset
