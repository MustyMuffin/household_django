from django import template

register = template.Library()

@register.filter
def is_privileged(user):
    return user.is_authenticated and user.groups.filter(name='Privileged').exists()