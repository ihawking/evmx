from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from guardian.shortcuts import assign_perm

from common.fields import ChecksumAddressField
from common.utils.crypto import generate_random_code


class Project(models.Model):
    owner = models.OneToOneField(
        "users.User",
        on_delete=models.CASCADE,
        related_name="project",
        verbose_name=_("管理人"),
    )
    appid = models.CharField(max_length=255, unique=True, blank=True)
    name = models.CharField(
        verbose_name=_("项目名称"),
        max_length=16,
        unique=True,
    )
    ip_white_list = models.TextField(
        _("IP白名单"),
        help_text="只有符合白名单的 IP 才可以与本网关交互; 支持 IP 地址或 IP 网段; "
        "可同时设置多个,中间用英文逗号','分割;",
    )
    webhook = models.URLField(
        _("通知地址"),
        max_length=256,
        help_text="用于本网关发送通知到项目后端;",
    )
    notification_failed_times = models.PositiveIntegerField(
        verbose_name=_("通知失败数"),
        default=0,
        editable=False,
    )
    next_notification_time = models.DateTimeField(auto_now_add=True, editable=False)

    pre_notify = models.BooleanField(
        _("开启预通知"),
        default=False,
        help_text="刚出块的时候通知一次",
    )
    hmac_key = models.CharField(
        _("HMAC密钥"),
        max_length=256,
        help_text="用于本网关接口签名;",
        blank=True,
    )
    system_account = models.OneToOneField(
        "chains.Account",
        on_delete=models.PROTECT,
        verbose_name=_("系统账户"),
        help_text="提币时,系统通过此账户发送代币到用户地址; "
        "要保证此地址的 Gas 和各代币充盈,否则提币无法成功;",
        related_name="project",
        blank=True,
    )
    collection_address = ChecksumAddressField(
        verbose_name=_("代币归集地址"),
        help_text="1.充值代币 2.合约支付,将自动归集到此地址; 差额支付地址需要去后台支付栏目单独设置;",
    )

    gather_worth = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        verbose_name="自动归集价值(USD)",
        default=10,
        help_text="某充币地址中,若某代币的价值大于此,则自动归集;",
        blank=True,
    )
    gather_time = models.PositiveIntegerField(
        verbose_name="自动归集周期(日)",
        default=32,
        help_text="某充币地址中,若某代币大于此周期未进行归集操作,则自动归集;",
        blank=True,
    )
    minimal_gather_worth = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        verbose_name="最小归集价值(USD)",
        default=1,
        help_text="充币地址中,若某代币的价值小于此,即使满足自动归集的条件,也不会执行归集操作; "
        "此值是为了防止Gas成本大于归集代币的价值;",
        blank=True,
    )
    active = models.BooleanField(verbose_name=_("启用"), default=True)

    class Meta:
        ordering = ("id",)
        verbose_name = "项目配置"
        verbose_name_plural = "项目配置"

    def __str__(self):
        return self.name

    @classmethod
    def generate(cls, owner):
        from chains.models import Account

        project = Project.objects.create(
            owner=owner,
            name=f"项目-{owner.username}",
            appid=f"EVMx-{generate_random_code(length=16, readable=True)}",
            system_account=Account.generate(),
            hmac_key=generate_random_code(length=32),
        )
        return project

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        assign_perm("change_project", self.owner, self)
        assign_perm("view_project", self.owner, self)

    @property
    def has_collection_address_for_differ(self):
        from invoices.models import CollectionAddressForDiffer

        return CollectionAddressForDiffer.objects.filter(project=self).exists()

    @classmethod
    def retrieve(cls, appid: str | None):
        if not appid:
            return cls.objects.get(pk=1)
        return cls.objects.get(appid=appid)

    @property
    def is_ready(self) -> (bool, str):
        if not self.ip_white_list:
            return False, _("项目IP白名单未设置")
        if not self.webhook:
            return False, _("项目通知地址未设置")
        if not self.collection_address:
            return False, _("项目代币归集地址未设置")
        if not self.active:
            return False, _("项目未启用")
        return True, ""

    @property
    def system_address(self):
        return self.system_account.address

    def recharge_gas_to(self, chain, account):
        from chains.models import TxType

        self.system_account.send_token(
            chain=chain,
            token=chain.currency,
            to=account.address,
            value=int(chain.erc20_transfer_cost * 5),
            tx_type=TxType.GasRecharging,
        )


def status(request):
    return ""


@receiver(pre_save, sender=Project)
def project_created(sender, instance: Project, **kwargs):
    created = not Project.objects.filter(pk=instance.pk).exists()

    if created:
        from chains.models import Account

        if not instance.hmac_key:
            instance.hmac_key = generate_random_code(length=32)

        instance.system_account = Account.generate()

        instance.appid = f"EVMx-{generate_random_code(length=16, readable=True)}"
