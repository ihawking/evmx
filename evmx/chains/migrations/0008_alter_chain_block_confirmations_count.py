# Generated by Django 4.2.14 on 2024-08-07 07:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chains", "0007_delete_historicalchain"),
    ]

    operations = [
        migrations.AlterField(
            model_name="chain",
            name="block_confirmations_count",
            field=models.PositiveSmallIntegerField(
                blank=True,
                default=18,
                help_text="交易的确认区块数越多,则该交易在区块链中埋的越深,就越不容易被篡改;<br>高于此确认数,系统将认定此交易被区块链最终接受;数值参考:ETH: 12; BSC: 15; Others: 16;",
                verbose_name="区块确认数量",
            ),
        ),
    ]
