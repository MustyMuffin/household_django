from chores.models import Chore
from django import template

register = template.Library()

@register.filter
def milestone_label(value):
    labels = {
        'books_read': 'Books Read',
        'words_read': 'Words Read',
        'earned_wage': 'Earned Wage',
    }

    if hasattr(value, 'text'):  # Handle Chore object
        return value.text

    try:
        chore = Chore.objects.get(pk=value)
        return chore.text
    except (Chore.DoesNotExist, ValueError, TypeError):
        pass

    return labels.get(value, str(value).replace('_', ' ').title())
