# Generated by Django 4.2.14 on 2024-07-25 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("withdrawals", "0002_alter_withdrawal_no_alter_withdrawal_unique_together"),
    ]

    operations = [
        migrations.AlterField(
            model_name="withdrawal",
            name="no",
            field=models.CharField(max_length=64, verbose_name="商户单号"),
        ),
    ]