from .models import Notification, UserSettings


def create_notification(user, notification_type, title, message, link='', metadata=None):
    settings, _ = UserSettings.objects.get_or_create(user=user)
    if not settings.push_notifications:
        return None
    if (
        notification_type in {Notification.Type.COMMENT, Notification.Type.LIKE}
        and not settings.community_notifications
    ):
        return None
    if (
        notification_type == Notification.Type.RECOMMENDATION
        and not settings.recommendation_notifications
    ):
        return None
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link,
        metadata=metadata or {},
    )
