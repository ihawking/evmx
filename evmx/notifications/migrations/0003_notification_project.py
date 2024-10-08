# Generated by Django 4.2.14 on 2024-07-23 07:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("globals", "0006_historicalproject_owner_project_owner"),
        ("notifications", "0002_remove_notification_project"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="project",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="globals.project",
                verbose_name="项目",
            ),
            preserve_default=False,
        ),
    ]
