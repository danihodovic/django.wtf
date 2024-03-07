from django import template

register = template.Library()


@register.filter
def to_percent(obj):
    if obj:
        if obj > 10:
            return f"{obj:.0f}%"
        return f"{obj:.2f}%"
    return ""
