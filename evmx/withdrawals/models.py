from django.db import models
from django.utils.translation import gettext_lazy as _
from guardian.shortcuts import assign_perm

from common.fields import ChecksumAddressField
from tokens.models import PlayerTokenValue


class Withdrawal(PlayerTokenValue):
    project = models.ForeignKey(
        "globals.Project",
        on_delete=models.CASCADE,
        verbose_name=_("项目"),
    )
    no = models.CharField(_("商户单号"), max_length=64)
    to = ChecksumAddressField(verbose_name=_("收币地址"))
    transaction_queue = models.OneToOneField(
        "chains.TransactionQueue",
        on_delete=models.PROTECT,
        verbose_name=_("执行队列"),
    )

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        unique_together = (("project", "no"),)
        verbose_name = _("提币")
        verbose_name_plural = _("提币")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        assign_perm("view_withdrawal", self.project.owner, self)

    @property
    def status(self):
        if not self.transaction_queue.transacted_at:
            return "待提币"
        if (
            self.transaction_queue.transaction
            and self.transaction_queue.transaction.block.confirmed
        ):
            return "已完成"
        return "确认中"

    @property
    def notification_content(self):
        return {
            "action": "withdrawal",
            "no": self.no,
        }
