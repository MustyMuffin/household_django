from .models import Notification

def unread_notifications(request):
    if request.user.is_authenticated:
        return {
            "unread_count": Notification.objects.filter(user=request.user, read=False).count(),
            "recent_notifications": Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        }
    return {}