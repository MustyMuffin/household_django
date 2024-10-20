from django.shortcuts import render

def index(request):
    """The home page for Household."""
    return render(request, 'household_main/index.html')