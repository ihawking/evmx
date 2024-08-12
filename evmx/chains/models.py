import datetime
import json
import time
from decimal import Decimal

import eth_abi
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction as db_transaction
from django.db.models import F
from django.db.models import Sum
from django.db.models.signals import post_save
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from guardian.shortcuts import assign_perm
from web3 import AsyncWeb3
from web3 import Web3
from web3.auto import w3 as auto_w3
from web3.datastructures import AttributeDict
from web3.exceptions import ExtraDataLengthError
from web3.exceptions import TransactionNotFound
from web3.middleware import async_geth_poa_middleware
from web3.middleware import geth_poa_middleware
from web3.types import ChecksumAddress
from web3.types import HexStr

from chains.constants import ERC20_TRANSFER_GAS
from chains.constants import ERC20_TRANSFER_STARTS
from chains.constants import gas_limit
from chains.utils import chain_icon_url
from chains.utils import chain_metadata
from common.consts import CALCULATE_BLOCK_TIME_COUNT
from common.decorators import cache_func
from common.fields import ChecksumAddressField
from common.fields import HexStr64Field
from common.utils.crypto import aes_cipher
from globals.models import Project
from invoices.models import Invoice
from invoices.models import InvoiceType
from invoices.models import Payment
from notifications.models import Notification
from tokens.models import Balance
from tokens.models import Token
from tokens.models import TokenAddress
from tokens.models import TokenType


# Create your models here.
class Chain(models.Model):
    chain_id = models.PositiveIntegerField(_("Chain ID"), blank=True, primary_key=True)
    name = models.CharField(_("名称"), max_length=32, unique=True, blank=True)
    currency = models.ForeignKey(
        "tokens.Token",
        verbose_name="原生币",
        on_delete=models.PROTECT,
        blank=True,
        related_name="chains_as_currency",
    )
    is_poa = models.BooleanField(_("是否为 POA 网络"), blank=True, editable=False)
    endpoint_uri = models.CharField(
        _("HTTP RPC 节点地址"),
        help_text="只需填写 RPC 地址,会自动识别公链信息",
        max_length=256,
        unique=True,
    )

    block_confirmations_count = models.PositiveSmallIntegerField(
        verbose_name=_("区块确认数量"),
        default=18,
        blank=True,
        help_text="交易的确认区块数越多,则该交易在区块链中埋的越深,就越不容易被篡改;<br>"
        "高于此确认数,系统将认定此交易被区块链最终接受;"
        "数值参考:ETH: 12; BSC: 15; Others: 16;",
    )
    active = models.BooleanField(
        default=True,
        verbose_name=_("启用"),
        help_text="关闭将会停止监听此链出块信息,且停止与其相关的接口调用",
    )

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        ordering = ("chain_id",)
        verbose_name = _("公链")
        verbose_name_plural = _("公链")

    def __str__(self):
        return f"{self.name}"

    @property
    @cache_func(timeout=32, use_params=True)
    def block_mining_time(self):
        blocks = Block.objects.filter(chain=self).order_by("-number")[
            :CALCULATE_BLOCK_TIME_COUNT
        ]
        if blocks.count() < CALCULATE_BLOCK_TIME_COUNT:
            return 16

        return (blocks[0].timestamp - blocks[31].timestamp) / CALCULATE_BLOCK_TIME_COUNT

    @property
    def is_ready(self):
        return Block.objects.filter(chain=self).exists()

    @property
    def icon(self):
        return chain_icon_url(self.chain_id)

    @property
    def gas_price(self) -> int:
        return self.w3.eth.gas_price

    @property
    def erc20_transfer_cost(self):
        return ERC20_TRANSFER_GAS * self.gas_price

    def is_contract(self, address: ChecksumAddress):
        return self.w3.eth.get_code(address).hex() != "0x"

    def get_balance(self, address: ChecksumAddress) -> int:
        return self.w3.eth.get_balance(address)

    def get_transaction_receipt(self, tx_hash: HexStr) -> dict:
        return json.loads(Web3.to_json(self.w3.eth.get_transaction_receipt(tx_hash)))

    def get_transaction(self, tx_hash: HexStr) -> dict:
        return json.loads(Web3.to_json(self.w3.eth.get_transaction(tx_hash)))

    def get_block(self, block_number: int) -> dict:
        return json.loads(Web3.to_json(self.w3.eth.get_block(block_number)))

    def get_block_number(self) -> int:
        return self.w3.eth.get_block_number()

    def is_block_number_confirmed(self, block_number):
        return block_number + self.block_confirmations_count < self.get_block_number()

    def is_transaction_should_be_processed(self, tx: dict) -> bool:
        if (
            tx["input"].startswith(ERC20_TRANSFER_STARTS)
            and TokenAddress.objects.filter(
                chain=self,
                address=tx["to"],
                token__type=TokenType.ERC20,
            ).exists()
        ):  # 平台所支持的 ERC20 代币的转账 (transfer)
            return True

        if Invoice.objects.filter(
            pay_address=tx["to"],
            transaction_queue__transaction__isnull=True,
        ).exists():  # 转入 ETH 到平台内的账单地址,且账单合约未失效
            return True

        if Account.objects.filter(
            address=tx["from"],
        ).exists():  # 平台内部账户发起的交易
            return True

        return Account.objects.filter(
            address=tx["to"],
        ).exists()  # 转入 ETH 到平台内部账户

    def is_transaction_packed(self, tx_hash: HexStr) -> bool:
        try:
            self.get_transaction_receipt(tx_hash)
        except TransactionNotFound:
            return False
        else:
            return True

    def is_transaction_confirmed(self, tx_hash: HexStr) -> bool:
        receipt = self.get_transaction_receipt(tx_hash)
        return self.is_block_number_confirmed(receipt["blockNumber"])

    def is_block_confirmed(self, block_number: int, block_hash: HexStr) -> bool:
        return self.get_block(block_number)["hash"] == block_hash

    @property
    def w3(self):
        w3 = Web3(Web3.HTTPProvider(self.endpoint_uri))
        if self.is_poa:
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        return w3

    @property
    def async_w3(self):
        aw3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(self.endpoint_uri))
        if self.is_poa:
            aw3.middleware_onion.inject(async_geth_poa_middleware, layer=0)

        return aw3

    @property
    def get_is_poa(self) -> bool:
        try:
            self.w3.eth.get_block("latest")

        except ExtraDataLengthError:
            return True

        else:
            return False

    @property
    def max_block_in_db(self) -> int:
        return Block.objects.filter(chain=self).order_by("-number").first().number

    @property
    async def amax_block_in_db(self) -> int | None:
        max_block = await Block.objects.filter(chain=self).order_by("-number").afirst()
        return max_block.number if max_block else None

    async def need_aligned(
        self,
        block_datas: list[AttributeDict],
    ) -> tuple[bool, int, int]:
        if not block_datas:
            return False, 0, 0

        current_number = block_datas[0]["number"]
        max_block_in_db = await self.amax_block_in_db

        if max_block_in_db and current_number > max_block_in_db + 31:
            return True, max_block_in_db + 1, max_block_in_db + 32

        return False, 0, 0


@receiver(post_save, sender=Chain)
def chains_changed(*args, **kwargs):
    cache.set(key="chains_changed", value=True)


@receiver(pre_save, sender=Chain)
@db_transaction.atomic
def chain_fill_up(sender, instance: Chain, **kwargs):
    if not Chain.objects.filter(pk=instance.pk).exists():
        instance.is_poa = instance.get_is_poa
        instance.chain_id = instance.w3.eth.chain_id

        metadata = chain_metadata(instance.chain_id)
        if not metadata:
            msg = "不支持此网络."
            raise ValidationError(msg)

        instance.name = metadata["name"]

        try:
            token = Token.objects.get(symbol=metadata["currency"]["symbol"])
            if (
                token.decimals != metadata["currency"]["decimals"]
                or token.type != TokenType.Native
            ):
                msg = "此网络的原生币与系统中已存在的代币冲突."
                raise ValidationError(msg)
        except Token.DoesNotExist:
            token = Token.objects.create(
                symbol=metadata["currency"]["symbol"],
                decimals=metadata["currency"]["decimals"],
                type=TokenType.Native,
            )
        instance.currency = token

        TokenAddress.objects.create(
            token=instance.currency,
            chain=instance,
            address="0x0000000000000000000000000000000000000000",
        )


class Block(models.Model):
    hash = HexStr64Field(verbose_name="哈希值")
    parent = models.OneToOneField(
        "chains.Block",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="父区块",
    )
    chain = models.ForeignKey(
        "chains.Chain",
        on_delete=models.CASCADE,
        verbose_name="公链",
    )
    number = models.PositiveIntegerField(db_index=True, verbose_name="区块号")
    timestamp = models.PositiveIntegerField(verbose_name="时间戳")

    confirmed = models.BooleanField(default=False, verbose_name="已确认")

    class Meta:
        ordering = (
            "chain",
            "-number",
        )
        unique_together = (
            "chain",
            "number",
        )
        verbose_name = _("区块")
        verbose_name_plural = _("区块")

    def __str__(self):
        return f"{self.chain.name}-{self.number}"

    @property
    def status(self):
        return "已确认" if self.confirmed else "确认中"

    @property
    def next_number(self):
        return self.number + 1

    @property
    def confirm_process(self):
        return (
            min(
                (
                    (self.chain.max_block_in_db - self.number)
                    / self.chain.block_confirmations_count
                ),
                1,
            )
            * 100
        )

    def confirm_with_transactions(self) -> bool:
        if self.confirmed:
            return True

        if (
            self.number + self.chain.block_confirmations_count
            > self.chain.max_block_in_db
        ):
            return False

        if self.chain.is_block_confirmed(
            block_number=self.number,
            block_hash=self.hash,
        ):
            self.confirmed = True
            self.save()
            transactions = self.transactions.all()
            for tx in transactions:
                tx.confirm()
            return True

        self.delete()
        return False


@receiver(pre_save, sender=Block)
def check_parent_block(sender, instance: Block, **kwargs):
    # 只需要创建区块时候进行验证
    if Block.objects.filter(pk=instance.pk).exists():
        return

    if instance.parent:
        if instance.number != instance.parent.number + 1:
            msg = "Block numbers must be consecutive."
            raise ValidationError(msg)

    elif Block.objects.filter(
        chain=instance.chain,
        number__lt=instance.number,
    ).exists():
        msg = "No parent block, but the chain is not empty."
        raise ValidationError(msg)


@receiver(post_save, sender=Block)
def block_created(sender, instance, created, **kwargs):
    if created:
        from chains.tasks import confirm_the_block

        confirm_the_block.apply_async(
            (instance.pk,),
            countdown=instance.chain.block_confirmations_count
            * instance.chain.block_mining_time
            + 4,
        )


class TxType(models.TextChoices):
    Paying = "paying", "💳 支付账单"
    Depositing = "depositing", "💰 充币"
    Withdrawal = "withdrawal", "🏧 提币"

    Funding = "funding", "🏦 注入资金"
    GasRecharging = "gas_recharging", "⛽ Gas分发"
    DepositGathering = "d_gathering", "💵 充币归集"
    InvoiceGathering = "i_gathering", "🧾 账单归集"


class Transaction(models.Model):
    project = models.ForeignKey(
        "globals.Project",
        on_delete=models.CASCADE,
        verbose_name=_("项目"),
        null=True,
    )
    block = models.ForeignKey(
        "chains.Block",
        on_delete=models.PROTECT,
        related_name="transactions",
        verbose_name=_("区块"),
    )
    hash = HexStr64Field()
    transaction_index = models.PositiveSmallIntegerField()
    metadata = models.JSONField()
    receipt = models.JSONField()

    type = models.CharField(
        _("类型"),
        max_length=16,
        choices=TxType.choices,
        blank=True,
    )

    class Meta:
        ordering = ("block", "transaction_index")
        verbose_name = _("交易")
        verbose_name_plural = _("交易")

    def __str__(self):
        return self.hash

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.project:
            assign_perm("view_transaction", self.project.owner, self)

    def initialize(self):
        if not self.link_transaction_queue() and not self.parse_external_transaction():
            self.delete()
            return

        if self.project.pre_notify:
            self.notify(as_pre=True)

    @db_transaction.atomic
    def confirm(self):
        self.notify()
        self.update_account_balance()

    def link_transaction_queue(self):
        try:
            transaction_queue = TransactionQueue.objects.get(
                chain=self.block.chain,
                account__address=self.metadata["from"],
                nonce=self.metadata["nonce"],
            )

            transaction_queue.transaction = self
            transaction_queue.save()

            self.project = transaction_queue.account.related_project
            self.type = transaction_queue.type
            self.save()

        except TransactionQueue.DoesNotExist:
            return False

        else:
            return True

    @property
    @cache_func(timeout=600, use_params=True)
    def token_transfer(self):
        if not self.success:
            return None

        from chains.utils.transactions import TokenTransferTuple
        from chains.utils.transactions import TransactionParser

        if hasattr(self, "transaction_queue") and hasattr(
            self.transaction_queue,
            "invoice",
        ):  # 部署账单合约,是特殊情况,因为无法通过解析交易得到内部转账信息
            invoice = self.transaction_queue.invoice
            return TokenTransferTuple(
                token=invoice.token,
                from_address=invoice.pay_address,
                to_address=invoice.collection_address,
                value=Payment.objects.filter(invoice=invoice).aggregate(
                    total=Sum("value"),
                )["total"],
            )

        return TransactionParser(self).token_transfer

    @db_transaction.atomic
    def parse_external_transaction(self):
        if not self.success:
            return False

        # 排除 gas 充值的情况下,向平台内部绑定了用户的账户转币,代表充值
        account = (
            Account.objects.filter(
                address=self.token_transfer.to_address,
                player__isnull=False,
            )
            .select_related("player__project")
            .first()
        )
        if account:
            self.project = account.player.project
            self.type = TxType.Depositing
            self.save()
            self.parse_depositing()
            return True

        # 系统账户接收代币,代表注入资金到系统账户
        project = Project.objects.filter(
            system_account__address=self.token_transfer.to_address,
        ).first()
        if project:
            self.project = project
            self.type = TxType.Funding
            self.save()
            return True

        now = timezone.now()
        # 如果接收代币的是合约账单地址
        contract_invoice = (
            Invoice.objects.filter(
                type=InvoiceType.Contract,
                expired_time__gte=now,
                pay_address=self.token_transfer.to_address,
                token=self.token_transfer.token,
                chain=self.block.chain,
                transaction_queue__transaction__isnull=True,
            )
            .select_related("project")
            .first()
        )
        if contract_invoice:
            self.parse_paying(contract_invoice)
            return True

        # 如果接收代币的是差额账单地址
        differ_invoice = (
            Invoice.objects.filter(
                type=InvoiceType.Differ,
                expired_time__gte=now,
                paid=False,
                pay_address=self.token_transfer.to_address,
                token=self.token_transfer.token,
                chain=self.block.chain,
                value=Decimal(self.token_transfer.value)
                / Decimal(
                    10**self.token_transfer.token.decimals,
                ),
            )
            .select_related("project")
            .first()
        )
        if differ_invoice:
            self.parse_paying(differ_invoice)
            return True

        return False

    def parse_depositing(self):
        from deposits.models import Deposit

        Deposit.parse_transaction(self)

    def parse_paying(self, invoice: Invoice):
        self.project = invoice.project
        self.type = TxType.Paying
        self.save()
        Payment.objects.create(
            transaction=self,
            invoice=invoice,
            value=self.token_transfer.value,
        )

    @db_transaction.atomic
    def update_account_balance(self):
        try:  # 扣 Gas
            account_as_tx_from = Account.objects.get(address=self.metadata["from"])
            account_as_tx_from.alter_balance(
                chain=self.block.chain,
                token=self.block.chain.currency,
                value=-(self.metadata["gasPrice"] * self.receipt["gasUsed"]),
            )
        except Account.DoesNotExist:
            pass

        if self.success:  # 成功了才会统计本次转币
            try:
                account_as_from = Account.objects.get(
                    address=self.token_transfer.from_address,
                )
                account_as_from.alter_balance(
                    chain=self.block.chain,
                    token=self.token_transfer.token,
                    value=-self.token_transfer.value,
                )
            except Account.DoesNotExist:
                pass

            try:
                account_as_to = Account.objects.get(
                    address=self.token_transfer.to_address,
                )
                account_as_to.alter_balance(
                    chain=self.block.chain,
                    token=self.token_transfer.token,
                    value=self.token_transfer.value,
                )
            except Account.DoesNotExist:
                pass

    @property
    def confirm_process(self):
        return self.block.confirm_process

    @property
    def success(self):
        return self.receipt["status"] == 1

    @property
    def withdrawal(self):
        return self.transaction_queue.withdrawal

    @property
    def tx_data(self) -> dict:
        return {
            "chain_id": self.block.chain.chain_id,
            "block": self.block.number,
            "hash": self.hash,
            "timestamp": self.block.timestamp,
            "confirmed": self.block.confirmed,
        }

    @property
    def datetime(self):
        return datetime.datetime.fromtimestamp(
            self.block.timestamp,
            tz=timezone.get_current_timezone(),
        )

    def notify(self, *, as_pre=False):
        if not self.success:
            return

        content = self.tx_data

        if as_pre and content["confirmed"]:  # 如果是预通知,那就只会通知确认中的区块交易
            return

        if self.type == TxType.Paying:
            if self.payment.invoice.paid:  # 本次支付账单支付进度完成,才会进行通知
                content.update(self.payment.invoice.notification_content)
            else:
                return
        elif self.type == TxType.Depositing:
            content.update(self.deposit.notification_content)
        elif self.type == TxType.Withdrawal:
            content.update(self.withdrawal.notification_content)
        else:
            return

        Notification.objects.create(
            project=self.project,
            transaction=self,
            content=content,
        )


class Account(models.Model):
    address = ChecksumAddressField(_("地址"), unique=True, db_index=True)
    encrypted_private_key = models.TextField(editable=False)

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("账户(EVM)")
        verbose_name_plural = _("账户(EVM)")

    def __str__(self):
        return f"{self.address}-{self.type}"

    @property
    def is_system_account(self):
        return Project.objects.filter(system_account=self).exists()

    @property
    def related_project(self):
        if self.is_system_account:
            return self.project
        return self.player.project

    @classmethod
    def generate(cls):
        acc = auto_w3.eth.account.create()

        return cls.objects.create(
            address=acc.address,
            encrypted_private_key=aes_cipher.encrypt(acc.key.hex()),
        )

    @property
    def private_key(self):
        return aes_cipher.decrypt(self.encrypted_private_key)

    @property
    def type(self):
        if hasattr(self, "player"):
            return _("充币账户")

        return _("系统账户")

    def gather(self, chain, token):
        balance = Balance.objects.get(account=self, chain=chain, token=token)

        balance.last_gathered_at = timezone.now()
        balance.save()

        if self.recharge_gas(chain):
            return

        value = balance.value

        if chain.currency == token:
            # 主币不能一次性清空,需要预留用作Gas
            value -= chain.erc20_transfer_cost * 5
            if value <= 0:
                return
        self.send_token(
            chain=chain,
            token=token,
            to=self.player.project.collection_address,
            value=int(value),
            tx_type=TxType.DepositGathering,
        )

    def recharge_gas(self, chain) -> bool:
        # 当本账户在某链上的主币余额不足转1次ERC20,则主动给此账户充值gas
        if self.balance(chain) <= chain.erc20_transfer_cost:
            self.player.project.recharge_gas_to(chain, self)
            return True
        return False

    def alter_balance(self, chain, token, value: int):
        balance, _ = Balance.objects.select_for_update().get_or_create(
            account=self,
            chain=chain,
            token=token,
        )

        balance.value = F("value") + value
        balance.save()

    @property
    def is_locked(self):
        return cache.get(f"lock_account_{self.address}")

    def get_lock(self):
        while True:
            if self.is_locked:
                time.sleep(0.02)
            else:
                return cache.set(
                    key=f"lock_account_{self.address}",
                    value=True,
                    timeout=10,
                )

    def release_lock(self):
        cache.delete(f"lock_account_{self.address}")

    def balance(self, chain: Chain) -> int:
        return chain.get_balance(self.address)

    def nonce(self, chain: Chain) -> int:
        return TransactionQueue.objects.filter(chain=chain, account=self).count()

    def _send_eth(self, chain: Chain, to: ChecksumAddress, value: int, tx_type: TxType):
        self.get_lock()
        queue = TransactionQueue.objects.create(
            type=tx_type,
            account=self,
            chain=chain,
            to=to,
            value=value,
            nonce=self.nonce(chain),
        )
        self.release_lock()

        return queue

    @staticmethod
    def get_erc20_transfer_data(to: ChecksumAddress, value: int) -> HexStr:
        encoded_params = eth_abi.encode(
            ["address", "uint256"],
            [
                to,
                value,
            ],
        )

        return ERC20_TRANSFER_STARTS + encoded_params.hex()

    def send_token(self, chain, token, to, value, tx_type):
        if chain.currency == token:
            return self._send_eth(chain, to, value, tx_type)

        token_address = TokenAddress.objects.get(
            chain=chain,
            token=token,
        ).address

        self.get_lock()
        queue = TransactionQueue.objects.create(
            type=tx_type,
            account=self,
            chain=chain,
            to=token_address,
            nonce=self.nonce(chain),
            data=self.get_erc20_transfer_data(to, value),
        )
        self.release_lock()

        return queue

    def delete(self, *args, **kwargs):
        msg = _("为保护数据完整性,禁止删除.")
        raise ValidationError(msg)

    # 如果你想确保批量删除也被阻止,可以覆盖 delete 方法
    @classmethod
    def delete_queryset(cls, queryset):
        msg = _("为保护数据完整性,禁止删除.")
        raise ValidationError(msg)


class TransactionQueue(models.Model):
    chain = models.ForeignKey(
        "chains.Chain",
        on_delete=models.PROTECT,
        verbose_name=_("网络"),
    )
    type = models.CharField(_("类型"), max_length=16, choices=TxType.choices)

    account = models.ForeignKey(
        "chains.Account",
        on_delete=models.PROTECT,
        verbose_name=_("账户"),
    )
    nonce = models.PositiveIntegerField(_("Nonce"))
    to = ChecksumAddressField(_("To"))
    value = models.DecimalField(_("Value"), max_digits=36, decimal_places=0, default=0)
    data = models.TextField(_("Data"), blank=True)

    transaction = models.OneToOneField(
        "chains.Transaction",
        on_delete=models.SET_NULL,
        verbose_name=_("交易"),
        null=True,
        related_name="transaction_queue",
    )

    transacted_at = models.DateTimeField(_("执行时间"), blank=True, null=True)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        unique_together = (
            "account",
            "chain",
            "nonce",
        )

        ordering = ("created_at",)

        verbose_name = _("执行队列")
        verbose_name_plural = verbose_name

    def __str__(self):
        if self.transaction:
            return self.transaction.hash

        return f"{self.chain.name}-{self.account.address}-{self.nonce}"

    @property
    def status(self):
        if not self.transacted_at:
            return "待执行"
        if self.transacted_at and not self.transaction:
            return "待上链"

        return self.transaction.block.status

    def generate_transaction_dict(self) -> dict:
        return {
            "chainId": self.chain.chain_id,
            "nonce": self.nonce,
            "from": self.account.address,
            "to": self.to,
            "value": int(self.value),
            "data": self.data if self.data else b"",
            "gas": gas_limit(
                deploy=self.data and not self.data.startswith(ERC20_TRANSFER_STARTS),
                base=int(self.value) != 0,
            ),
            "gasPrice": self.chain.gas_price,
        }

    def transact(self):
        """
        执行本次交易
        :return:
        """

        self.transacted_at = timezone.now()
        self.save()

        signed_transaction = self.chain.w3.eth.account.sign_transaction(
            self.generate_transaction_dict(),
            self.account.private_key,
        )
        self.chain.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)

    def delete(self, *args, **kwargs):
        msg = _("为保护数据完整性,禁止删除.")
        raise ValidationError(msg)

    # 确保批量删除也被阻止,覆盖 delete 方法
    @classmethod
    def delete_queryset(cls, queryset):
        msg = _("为保护数据完整性,禁止删除.")
        raise ValidationError(msg)
