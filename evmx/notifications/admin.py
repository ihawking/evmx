from django.contrib import admin
from guardian.admin import GuardedModelAdmin

from common.admin import ModelAdmin
from notifications.models import Notification


# Register your models here.


@admin.register(Notification)
class NotificationAdmin(ModelAdmin, GuardedModelAdmin):
    list_display = (
        "project",
        "notified",
        "created_at",
    )

    user_can_access_owned_objects_only = True
    user_owned_objects_field = "project__owner"
