from django import template

register = template.Library()


@register.filter
def to_percent(obj):
    if obj:
        return f"{obj:.2%}"
    return obj
