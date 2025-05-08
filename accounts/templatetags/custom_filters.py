from django import template

register = template.Library()

@register.filter
def pluck(objects, field):
    return [getattr(obj, field) for obj in objects]

@register.filter
def unique(value):
    """Get unique items from a list."""
    return list(set(value))

@register.filter
def milestone_label(value):
    labels = {
        'books_read': 'Books Read',
        'words_read': 'Words Read',
        # 'specific_book': 'Specific Book',
        'earned_wage': 'Earned Wage',
    }
    return labels.get(value, value.replace('_', ' ').title())