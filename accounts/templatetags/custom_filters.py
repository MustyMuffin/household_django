from django import template

register = template.Library()

@register.filter
def pluck(objects, field):
    return [getattr(obj, field) for obj in objects]

@register.filter
def unique(value):
    """Get unique items from a list."""
    return list(set(value))