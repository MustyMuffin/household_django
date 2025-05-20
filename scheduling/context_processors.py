from .models import Notification

def unread_notifications(request):
    if request.user.is_authenticated:
        unread = request.user.notifications.filter(read=False).order_by('-created_at')[:5]
        return {
            'unread_notifications': unread,
            'unread_count': unread.count()
        }
    return {}