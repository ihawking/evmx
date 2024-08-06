# Generated by Django 4.2.14 on 2024-07-21 06:41

import django.db.models.deletion
import simple_history.models
from django.db import migrations, models

import common.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Account",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "address",
                    common.fields.ChecksumAddressField(
                        db_index=True, max_length=42, unique=True, verbose_name="地址"
                    ),
                ),
                ("encrypted_private_key", models.TextField(editable=False)),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
            ],
            options={
                "verbose_name": "本地账户",
                "verbose_name_plural": "本地账户",
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="Block",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "hash",
                    common.fields.HexStr64Field(
                        db_index=True, max_length=66, unique=True, verbose_name="哈希"
                    ),
                ),
                (
                    "number",
                    models.PositiveIntegerField(db_index=True, verbose_name="区块号"),
                ),
                ("timestamp", models.PositiveIntegerField(verbose_name="时间戳")),
                (
                    "confirmed",
                    models.BooleanField(default=False, verbose_name="已确认"),
                ),
            ],
            options={
                "verbose_name": "区块",
                "verbose_name_plural": "区块",
                "ordering": ("chain", "-number"),
            },
        ),
        migrations.CreateModel(
            name="Chain",
            fields=[
                (
                    "chain_id",
                    models.PositiveIntegerField(
                        blank=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="Chain ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True, max_length=32, unique=True, verbose_name="名称"
                    ),
                ),
                (
                    "is_poa",
                    models.BooleanField(
                        blank=True, editable=False, verbose_name="是否为 POA 网络"
                    ),
                ),
                (
                    "endpoint_uri",
                    models.CharField(
                        help_text="只需填写 RPC 地址,会自动识别公链信息",
                        max_length=256,
                        unique=True,
                        verbose_name="HTTP RPC 节点地址",
                    ),
                ),
                (
                    "block_confirmations_count",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        default=18,
                        help_text="交易的确认区块数越多,则该交易在区块链中埋的越深,就越不容易被篡改;高于此确认数,系统将认定此交易被区块链最终接受;数值参考:ETH: 12; BSC: 15; Others: 16;",
                        verbose_name="区块确认数量",
                    ),
                ),
                (
                    "active",
                    models.BooleanField(
                        default=True,
                        help_text="关闭将会停止监听此链出块信息,且停止与其相关的接口调用",
                        verbose_name="启用",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="更新时间"),
                ),
            ],
            options={
                "verbose_name": "公链",
                "verbose_name_plural": "公链",
                "ordering": ("chain_id",),
            },
        ),
        migrations.CreateModel(
            name="HistoricalChain",
            fields=[
                (
                    "chain_id",
                    models.PositiveIntegerField(
                        blank=True, db_index=True, verbose_name="Chain ID"
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True, db_index=True, max_length=32, verbose_name="名称"
                    ),
                ),
                (
                    "is_poa",
                    models.BooleanField(
                        blank=True, editable=False, verbose_name="是否为 POA 网络"
                    ),
                ),
                (
                    "endpoint_uri",
                    models.CharField(
                        db_index=True,
                        help_text="只需填写 RPC 地址,会自动识别公链信息",
                        max_length=256,
                        verbose_name="HTTP RPC 节点地址",
                    ),
                ),
                (
                    "block_confirmations_count",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        default=18,
                        help_text="交易的确认区块数越多,则该交易在区块链中埋的越深,就越不容易被篡改;高于此确认数,系统将认定此交易被区块链最终接受;数值参考:ETH: 12; BSC: 15; Others: 16;",
                        verbose_name="区块确认数量",
                    ),
                ),
                (
                    "active",
                    models.BooleanField(
                        default=True,
                        help_text="关闭将会停止监听此链出块信息,且停止与其相关的接口调用",
                        verbose_name="启用",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        blank=True, editable=False, verbose_name="创建时间"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        blank=True, editable=False, verbose_name="更新时间"
                    ),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
            ],
            options={
                "verbose_name": "historical 公链",
                "verbose_name_plural": "historical 公链",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="Transaction",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "hash",
                    common.fields.HexStr64Field(
                        db_index=True, max_length=66, unique=True, verbose_name="哈希"
                    ),
                ),
                ("transaction_index", models.PositiveSmallIntegerField()),
                ("metadata", models.JSONField()),
                ("receipt", models.JSONField()),
                (
                    "type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("paying", "💳 支付账单"),
                            ("depositing", "💰 充币"),
                            ("withdrawal", "🏧 提币"),
                            ("funding", "🏦 注入资金"),
                            ("gas_recharging", "⛽ Gas分发"),
                            ("d_gathering", "💵 充币归集"),
                            ("i_gathering", "🧾 账单归集"),
                        ],
                        max_length=16,
                        verbose_name="类型",
                    ),
                ),
                (
                    "block",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="transactions",
                        to="chains.block",
                    ),
                ),
            ],
            options={
                "verbose_name": "交易",
                "verbose_name_plural": "交易",
                "ordering": ("block", "transaction_index"),
            },
        ),
        migrations.CreateModel(
            name="TransactionQueue",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("paying", "💳 支付账单"),
                            ("depositing", "💰 充币"),
                            ("withdrawal", "🏧 提币"),
                            ("funding", "🏦 注入资金"),
                            ("gas_recharging", "⛽ Gas分发"),
                            ("d_gathering", "💵 充币归集"),
                            ("i_gathering", "🧾 账单归集"),
                        ],
                        max_length=16,
                        verbose_name="类型",
                    ),
                ),
                ("nonce", models.PositiveIntegerField(verbose_name="Nonce")),
                (
                    "to",
                    common.fields.ChecksumAddressField(
                        db_index=True, max_length=42, verbose_name="To"
                    ),
                ),
                (
                    "value",
                    models.DecimalField(
                        decimal_places=0, default=0, max_digits=36, verbose_name="Value"
                    ),
                ),
                ("data", models.TextField(blank=True, verbose_name="Data")),
                (
                    "transacted_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="执行时间"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="更新时间"),
                ),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="chains.account",
                        verbose_name="账户",
                    ),
                ),
                (
                    "chain",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="chains.chain",
                        verbose_name="网络",
                    ),
                ),
                (
                    "transaction",
                    models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="transaction_queue",
                        to="chains.transaction",
                        verbose_name="交易",
                    ),
                ),
            ],
            options={
                "verbose_name": "执行队列",
                "verbose_name_plural": "执行队列",
                "ordering": ("created_at",),
            },
        ),
    ]