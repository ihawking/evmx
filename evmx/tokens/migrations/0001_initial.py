# Generated by Django 4.2.14 on 2024-07-21 06:41

import django.db.models.deletion
import simple_history.models
from django.db import migrations, models

import common.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("chains", "0002_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Balance",
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
                    "value",
                    models.DecimalField(decimal_places=0, default=0, max_digits=36),
                ),
                ("last_gathered_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "余额",
                "verbose_name_plural": "余额",
            },
        ),
        migrations.CreateModel(
            name="HistoricalToken",
            fields=[
                (
                    "id",
                    models.BigIntegerField(
                        auto_created=True, blank=True, db_index=True, verbose_name="ID"
                    ),
                ),
                (
                    "symbol",
                    models.CharField(
                        db_index=True,
                        help_text="例如:USDT、UNI",
                        max_length=8,
                        verbose_name="代号",
                    ),
                ),
                (
                    "decimals",
                    models.PositiveSmallIntegerField(default=18, verbose_name="精度"),
                ),
                (
                    "coingecko_id",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        help_text="用于自动从Coingecko获取代币USD价格可以从Coingecko代币详情页面找到此值如果想手动设置价格,或者代币未上架Coingecko,则留空",
                        max_length=32,
                        null=True,
                        verbose_name="Coingecko API ID",
                    ),
                ),
                (
                    "price_in_usd",
                    models.DecimalField(
                        decimal_places=8,
                        default=0,
                        max_digits=32,
                        verbose_name="价格(USD)",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[("Native", "原生币"), ("ERC20", "ERC20")],
                        default="ERC20",
                        editable=False,
                        max_length=16,
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
                "verbose_name": "historical 代币",
                "verbose_name_plural": "historical 代币",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="Token",
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
                    "symbol",
                    models.CharField(
                        help_text="例如:USDT、UNI",
                        max_length=8,
                        unique=True,
                        verbose_name="代号",
                    ),
                ),
                (
                    "decimals",
                    models.PositiveSmallIntegerField(default=18, verbose_name="精度"),
                ),
                (
                    "coingecko_id",
                    models.CharField(
                        blank=True,
                        help_text="用于自动从Coingecko获取代币USD价格可以从Coingecko代币详情页面找到此值如果想手动设置价格,或者代币未上架Coingecko,则留空",
                        max_length=32,
                        null=True,
                        unique=True,
                        verbose_name="Coingecko API ID",
                    ),
                ),
                (
                    "price_in_usd",
                    models.DecimalField(
                        decimal_places=8,
                        default=0,
                        max_digits=32,
                        verbose_name="价格(USD)",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[("Native", "原生币"), ("ERC20", "ERC20")],
                        default="ERC20",
                        editable=False,
                        max_length=16,
                    ),
                ),
            ],
            options={
                "verbose_name": "代币",
                "verbose_name_plural": "代币",
            },
        ),
        migrations.CreateModel(
            name="TokenTransfer",
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
                    "from_address",
                    common.fields.ChecksumAddressField(
                        db_index=True, max_length=42, verbose_name="From"
                    ),
                ),
                (
                    "to_address",
                    common.fields.ChecksumAddressField(
                        db_index=True, max_length=42, verbose_name="To"
                    ),
                ),
                (
                    "value",
                    models.DecimalField(decimal_places=0, default=0, max_digits=36),
                ),
                (
                    "token",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="tokens.token"
                    ),
                ),
                (
                    "transaction",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="token_transfer",
                        to="chains.transaction",
                    ),
                ),
            ],
            options={
                "verbose_name": "转移",
                "verbose_name_plural": "转移",
            },
        ),
        migrations.CreateModel(
            name="TokenAddress",
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
                        db_index=True, max_length=42, verbose_name="代币地址"
                    ),
                ),
                (
                    "active",
                    models.BooleanField(
                        default=True,
                        help_text="关闭将会停止此链上与本代币相关接口的调用",
                        verbose_name="启用",
                    ),
                ),
                (
                    "chain",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="chains.chain",
                        verbose_name="公链",
                    ),
                ),
                (
                    "token",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="tokens.token",
                        verbose_name="代币",
                    ),
                ),
            ],
            options={
                "verbose_name": "代币地址",
                "verbose_name_plural": "代币地址",
            },
        ),
        migrations.AddField(
            model_name="token",
            name="chains",
            field=models.ManyToManyField(
                help_text="记录代币在每个公链上的地址,原生币地址默认为零地址",
                related_name="tokens",
                through="tokens.TokenAddress",
                to="chains.chain",
            ),
        ),
        migrations.CreateModel(
            name="HistoricalTokenAddress",
            fields=[
                (
                    "id",
                    models.BigIntegerField(
                        auto_created=True, blank=True, db_index=True, verbose_name="ID"
                    ),
                ),
                (
                    "address",
                    common.fields.ChecksumAddressField(
                        db_index=True, max_length=42, verbose_name="代币地址"
                    ),
                ),
                (
                    "active",
                    models.BooleanField(
                        default=True,
                        help_text="关闭将会停止此链上与本代币相关接口的调用",
                        verbose_name="启用",
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
                (
                    "chain",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="chains.chain",
                        verbose_name="公链",
                    ),
                ),
            ],
            options={
                "verbose_name": "historical 代币地址",
                "verbose_name_plural": "historical 代币地址",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]