# Generated by Django 4.2.14 on 2024-08-02 03:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
        ("deposits", "0003_deposit_project"),
    ]

    operations = [
        migrations.AlterField(
            model_name="deposit",
            name="player",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="users.player",
                verbose_name="用户",
            ),
        ),
    ]
