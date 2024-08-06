from celery import shared_task
from django.utils import timezone

from common.decorators import singleton_task
from notifications.models import Notification


@shared_task(ignore_result=True)
@singleton_task(timeout=32)
def notify():
    for notification in Notification.objects.filter(
        notified=False,
        project__next_notification_time__lte=timezone.now(),
    )[:4]:
        notification.notify()
