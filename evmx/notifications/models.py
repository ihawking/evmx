import requests
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from guardian.shortcuts import assign_perm
from loguru import logger

from common.consts import HTTP_OK
from common.utils.crypto import create_hmac_sign


# Create your models here.


class Notification(models.Model):
    project = models.ForeignKey(
        "globals.Project",
        on_delete=models.CASCADE,
        verbose_name=_("项目"),
    )
    transaction = models.ForeignKey(
        "chains.Transaction",
        on_delete=models.CASCADE,
        null=True,
    )

    content = models.JSONField()

    notified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    notified_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "回调通知"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.transaction.hash

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        assign_perm("view_notification", self.project.owner, self)

    def notify(self):
        project = self.transaction.project
        headers = {
            "EVMx-Signature": create_hmac_sign(
                message_dict=self.content,
                key=project.hmac_key,
            ),
        }

        try:
            resp = requests.post(
                project.webhook,
                data=self.content,
                headers=headers,
                timeout=4,
            )
            assert resp.status_code == HTTP_OK
            assert resp.text == "ok"

            self.notified = True
            self.notified_at = timezone.now()
            self.save()
            project.notification_failed_times = 0
            project.save()

        except Exception as e:
            logger.error(e)
            project.notification_failed_times += 1
            project.next_notification_time = timezone.now() + timezone.timedelta(
                seconds=min(2**project.notification_failed_times, 1800),
            )
            project.save()
