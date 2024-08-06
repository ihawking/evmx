# Generated by Django 4.2.14 on 2024-07-27 07:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chains", "0005_alter_account_options"),
        ("tokens", "0003_alter_tokentransfer_transaction"),
    ]

    operations = [
        migrations.AlterField(
            model_name="balance",
            name="account",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="chains.account",
                verbose_name="账户",
            ),
        ),
        migrations.AlterField(
            model_name="balance",
            name="chain",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="chains.chain",
                verbose_name="公链",
            ),
        ),
        migrations.AlterField(
            model_name="balance",
            name="token",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="tokens.token",
                verbose_name="代币",
            ),
        ),
        migrations.AlterField(
            model_name="balance",
            name="value",
            field=models.DecimalField(
                decimal_places=0, default=0, max_digits=36, verbose_name="数量(整数)"
            ),
        ),
        migrations.DeleteModel(
            name="TokenTransfer",
        ),
    ]