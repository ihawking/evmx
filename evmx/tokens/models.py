from django.db import models
from django.utils.translation import gettext_lazy as _

from common.fields import ChecksumAddressField
from globals.models import Project


# Create your models here.


class TokenType(models.TextChoices):
    Native = "Native", _("原生币")
    ERC20 = "ERC20", _("ERC20")


class Token(models.Model):
    symbol = models.CharField(
        _("代号"),
        max_length=8,
        help_text=_("例如:USDT、UNI"),
        unique=True,
    )
    decimals = models.PositiveSmallIntegerField(_("精度"), default=18)
    chains = models.ManyToManyField(
        "chains.Chain",
        through="tokens.TokenAddress",
        related_name="tokens",
        help_text="记录代币在每个公链上的地址,原生币地址默认为零地址",
    )

    coingecko_id = models.CharField(
        max_length=32,
        verbose_name="Coingecko API ID",
        help_text=_(
            "用于自动从Coingecko获取代币USD价格可以从Coingecko代币详情页面找到此值如果想手动设置价格,或者代币未上架Coingecko,则留空",
        ),
        unique=True,
        blank=True,
        null=True,
    )
    price_in_usd = models.DecimalField(
        _("价格(USD)"),
        default=0,
        max_digits=36,
        decimal_places=18,
    )
    type = models.CharField(
        choices=TokenType.choices,
        default=TokenType.ERC20,
        max_length=16,
        editable=False,
    )

    class Meta:
        verbose_name = _("代币")
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.symbol}"

    def gather_value(self, project: Project):
        if self.price_in_usd == 0:
            return 10000000000 * 10**self.decimals
        return project.gather_worth / self.price_in_usd * 10**self.decimals

    def minimal_gather_value(self, project: Project):
        if self.price_in_usd == 0:
            return 10000000000 * 10**self.decimals
        return project.minimal_gather_worth / self.price_in_usd * 10**self.decimals

    @property
    def is_currency(self):
        return self.type == TokenType.Native

    def support_this_chain(self, chain) -> bool:
        return TokenAddress.objects.filter(
            chain=chain,
            token=self,
            active=True,
        ).exists()

    def address(self, chain):
        try:
            return TokenAddress.objects.get(token=self, chain=chain).address
        except TokenAddress.DoesNotExist:
            return None


class TokenAddress(models.Model):
    token = models.ForeignKey(
        "tokens.Token",
        on_delete=models.CASCADE,
        verbose_name=_("代币"),
    )
    chain = models.ForeignKey(
        "chains.Chain",
        on_delete=models.CASCADE,
        verbose_name=_("公链"),
    )
    address = ChecksumAddressField(verbose_name=_("代币地址"), db_index=True)

    active = models.BooleanField(
        default=True,
        verbose_name="启用",
        help_text="关闭将会停止此链上与本代币相关接口的调用",
    )

    class Meta:
        unique_together = ("token", "chain")

        verbose_name = _("代币地址")
        verbose_name_plural = _("代币地址")

    def __str__(self):
        return f"{self.chain.name} - {self.token.symbol}"


class PlayerTokenValue(models.Model):
    player = models.ForeignKey(
        "users.Player",
        on_delete=models.PROTECT,
        verbose_name=_("用户"),
        blank=True,
        null=True,
    )
    token = models.ForeignKey(
        "tokens.Token",
        on_delete=models.PROTECT,
        verbose_name=_("代币"),
    )
    value = models.DecimalField(_("数量"), max_digits=36, decimal_places=18)
    worth = models.DecimalField(
        _("价值(USD)"),
        max_digits=16,
        decimal_places=2,
        default=0,
    )

    class Meta:
        abstract = True

    @classmethod
    def is_abstract_model(cls):
        return cls._meta.abstract


class Balance(models.Model):
    account = models.ForeignKey(
        "chains.Account",
        on_delete=models.PROTECT,
        verbose_name=_("账户"),
    )
    chain = models.ForeignKey(
        "chains.Chain",
        on_delete=models.PROTECT,
        verbose_name=_("公链"),
    )
    token = models.ForeignKey(
        "tokens.Token",
        on_delete=models.PROTECT,
        verbose_name=_("代币"),
    )
    value = models.DecimalField(
        max_digits=36,
        decimal_places=0,
        default=0,
        verbose_name=_("数量(整数)"),
    )

    last_gathered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            "account",
            "chain",
            "token",
        )
        verbose_name = _("余额")
        verbose_name_plural = _("余额")

    def __str__(self):
        return f"{self.account} - {self.chain.name} - {self.token.symbol}"

    @property
    def value_display(self):
        return f"{self.value / 10**self.token.decimals:.8f}"
