from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def chores(request):
    """Show all Chores."""
    # chores = Chores.objects.filter(owner=request.user).order_by('date_added')
    context = {'chores': chores}
    return render(request, 'chores/chores.html', context)