from decimal import Decimal
from typing import cast

from django.db import models
from django.db import transaction as db_transaction
from django.db.models import F
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from guardian.shortcuts import assign_perm
from web3.types import HexStr

from chains.utils import create2
from common.fields import ChecksumAddressField
from globals.models import Project


# Create your models here.


class InvoiceType(models.TextChoices):
    Differ = "differ", _("差额")
    Contract = "contract", _("合约")


class Invoice(models.Model):
    project = models.ForeignKey(
        "globals.Project",
        on_delete=models.CASCADE,
        verbose_name=_("项目"),
    )
    type = models.CharField(
        verbose_name=_("类型"),
        max_length=16,
        choices=InvoiceType.choices,
    )
    sys_no = models.CharField(
        verbose_name=_("系统单号"),
        unique=True,
        max_length=32,
        db_index=True,
    )
    no = models.CharField(
        verbose_name=_("商户单号"),
        max_length=32,
        db_index=True,
    )
    subject = models.CharField(_("标题"), max_length=32)
    detail = models.JSONField(_("详情"), default=dict)
    token = models.ForeignKey(
        "tokens.Token",
        on_delete=models.PROTECT,
        verbose_name=_("代币"),
    )
    chain = models.ForeignKey(
        "chains.Chain",
        on_delete=models.PROTECT,
        verbose_name=_("网络"),
    )
    original_value = models.DecimalField(
        verbose_name=_("原始数量"),
        max_digits=36,
        decimal_places=18,
        blank=True,
        null=True,
        help_text=_("通过接口创建账单的时候,参数中最初期望的应付数量value"),
    )
    value = models.DecimalField(
        verbose_name=_("应付数量"),
        max_digits=36,
        decimal_places=18,
        help_text=_("如果类型为Differ差额,应付数量可能在原始数量上下差额浮动."),
    )

    expired_time = models.DateTimeField(_("支付截止时间"))
    redirect_url = models.URLField(_("支付成功后重定向地址"), blank=True)

    salt = models.CharField(
        verbose_name=_("盐"),
        max_length=66,
        unique=True,
        blank=True,
        null=True,
    )
    init_code = models.TextField(  # noqa: DJ001
        verbose_name=_("合约初始化代码"),
        blank=True,
        null=True,
    )

    pay_address = ChecksumAddressField(verbose_name=_("账单支付地址"), db_index=True)
    collection_address = ChecksumAddressField(verbose_name=_("资金归集地址"))

    paid = models.BooleanField(_("支付完成"), default=False)
    actual_value = models.DecimalField(
        _("实收数量"),
        max_digits=36,
        decimal_places=18,
        default=0,
        help_text=_("如果类型为Contract合约,实收数量可能大于应付数量."),
    )

    transaction_queue = models.OneToOneField(
        "chains.TransactionQueue",
        on_delete=models.PROTECT,
        verbose_name=_("归集交易"),
        null=True,
        blank=True,
    )
    worth = models.DecimalField(
        _("价值(USD)"),
        max_digits=16,
        decimal_places=2,
        default=0,
    )

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        unique_together = (("project", "no"),)
        ordering = ("-created_at",)
        verbose_name = _("账单")
        verbose_name_plural = _("账单")

    def __str__(self):
        return f"{self.sys_no}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        assign_perm("view_invoice", self.project.owner, self)

    @classmethod
    def get_differ(
        cls,
        project: Project,
        value,
        differ_step,
        differ_max,
    ) -> (str | None, Decimal | None):
        now = timezone.now()
        max_step = int(differ_max / differ_step)

        addresses_for_differ = set(
            CollectionAddressForDiffer.objects.filter(project=project).values_list(
                "address",
                flat=True,
            ),
        )

        if not addresses_for_differ:
            addresses_for_differ = [project.collection_address]

        for step in range(max_step):
            differ_value_upper = value + step * differ_step
            differ_value_lower = value - step * differ_step

            if differ_value_lower <= 0:
                return None, None

            for address in addresses_for_differ:
                if not Invoice.objects.filter(
                    pay_address=address,
                    value=differ_value_upper,
                    expired_time__gte=now,
                    paid=False,
                ).exists():
                    return address, differ_value_upper

                if not Invoice.objects.filter(
                    pay_address=address,
                    value=differ_value_lower,
                    expired_time__gte=now,
                    paid=False,
                ).exists():
                    return address, differ_value_lower

        return None, None

    def manual_gather(self):
        if self.type == InvoiceType.Differ:
            return

    @property
    def status(self):
        if not self.paid:
            if timezone.now() > self.expired_time:
                return "已失效"
            return "待支付"
        if self.payment_set.filter(transaction__block__confirmed=False).exists():
            return "确认中"
        return "已支付"

    @property
    def notification_content(self):
        return {
            "action": "invoice",
            "sys_no": self.sys_no,
            "no": self.no,
            "original_value": str(self.original_value),
            "value": str(self.value),
            "actual_value": str(self.actual_value),
        }

    @property
    def token_symbol(self):
        return self.token.symbol

    @property
    def token_address(self):
        return self.token.address(self.chain)

    @property
    def gathered(self):
        return self.transaction_queue.transaction.block.confirmed

    @property
    def remaining_value(self) -> Decimal:
        # 待支付的数量
        return min(self.value - self.actual_value, Decimal("0"))

    @property
    def chain_id(self):
        return self.chain.chain_id

    def gather(self):
        from chains.models import TxType

        account = self.project.system_account

        account.get_lock()
        with db_transaction.atomic():
            from chains.models import TransactionQueue

            self.transaction_queue = TransactionQueue.objects.create(
                type=TxType.InvoiceGathering,
                account=account,
                chain=self.chain,
                to=create2.factory_address,
                nonce=account.nonce(self.chain),
                data=create2.get_transaction_data(
                    salt=cast(HexStr, self.salt),
                    init_code=cast(HexStr, self.init_code),
                ),
            )
            self.save()
        account.release_lock()


@receiver(post_save, sender=Invoice)
def calculate_worth(sender, instance: Invoice, created, **kwargs):
    if created:
        instance.worth = instance.token.price_in_usd * instance.value
        instance.save()


class Payment(models.Model):
    transaction = models.OneToOneField(
        "chains.Transaction",
        on_delete=models.CASCADE,
        verbose_name=_("交易"),
    )
    invoice = models.ForeignKey(
        "invoices.Invoice",
        on_delete=models.CASCADE,
        verbose_name=_("账单"),
    )
    value = models.DecimalField(_("支付数量"), max_digits=36, decimal_places=0)

    class Meta:
        ordering = ("transaction",)
        verbose_name = _("支付记录")
        verbose_name_plural = _("支付记录")

    def __str__(self):
        return f"{self.transaction} - {self.value}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        assign_perm("view_payment", self.invoice.project.owner, self)

    @property
    def confirm_process(self):
        return self.transaction.confirm_process

    @property
    def tx_hash(self):
        return self.transaction.hash

    @property
    def value_display(self):
        return Decimal(self.value) / Decimal(10**self.invoice.token.decimals)


@receiver(post_save, sender=Payment)
def create_payment(sender, instance: Payment, created, **kwargs):
    if created:
        invoice = instance.invoice
        invoice.actual_value = F("actual_value") + instance.value_display
        invoice.save()

        invoice.refresh_from_db()
        if invoice.actual_value >= invoice.value:
            invoice.paid = True
            invoice.save()


@receiver(post_delete, sender=Payment)
def delete_payment(sender, instance: Payment, **kwargs):
    invoice = instance.invoice
    invoice.actual_value = F("actual_value") - instance.value_display
    invoice.save()

    invoice.refresh_from_db()
    if invoice.actual_value < invoice.value:
        invoice.paid = False
        invoice.save()


class CollectionAddressForDiffer(models.Model):
    project = models.ForeignKey(
        "globals.Project",
        on_delete=models.CASCADE,
        verbose_name=_("项目"),
        editable=False,
        blank=True,
    )
    address = ChecksumAddressField(verbose_name="地址", unique=True)

    class Meta:
        verbose_name = _("差额支付地址")
        verbose_name_plural = _("差额支付地址")

    def __str__(self):
        return self.address

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        assign_perm("view_collectionaddressfordiffer", self.project.owner, self)
        assign_perm("delete_collectionaddressfordiffer", self.project.owner, self)
        assign_perm("change_collectionaddressfordiffer", self.project.owner, self)
