from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _
from guardian.shortcuts import assign_perm

from chains.models import Account
from chains.models import Transaction
from tokens.models import PlayerTokenValue


# Create your models here.


class Deposit(PlayerTokenValue):
    project = models.ForeignKey(
        "globals.Project",
        on_delete=models.CASCADE,
        verbose_name=_("项目"),
    )
    transaction = models.OneToOneField(
        "chains.Transaction",
        on_delete=models.CASCADE,
        verbose_name=_("交易"),
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("充币")
        verbose_name_plural = _("充币")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        assign_perm("view_deposit", self.project.owner, self)

    @property
    def status(self):
        return "已确认" if self.transaction.block.confirmed else "确认中"

    @classmethod
    def parse_transaction(cls, transaction: Transaction):
        token_transfer = transaction.token_transfer
        deposit_account = Account.objects.get(
            address=token_transfer.to_address,
            player__isnull=False,
        )
        Deposit.objects.create(
            project=transaction.project,
            transaction=transaction,
            player=deposit_account.player,
            token=token_transfer.token,
            value=Decimal(token_transfer.value)
            / Decimal(10**token_transfer.token.decimals),
        )

    @property
    def notification_content(self):
        return {
            "action": "deposit",
            "uid": self.player.uid,
            "symbol": self.token.symbol,
            "value": str(self.value),
        }
