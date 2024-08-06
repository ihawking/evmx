# Generated by Django 4.2.14 on 2024-08-02 05:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("withdrawals", "0004_alter_withdrawal_player"),
    ]

    operations = [
        migrations.AlterField(
            model_name="withdrawal",
            name="value",
            field=models.DecimalField(
                decimal_places=18, max_digits=36, verbose_name="数量"
            ),
        ),
    ]