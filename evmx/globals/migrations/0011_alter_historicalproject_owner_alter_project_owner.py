# Generated by Django 4.2.14 on 2024-07-31 08:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("globals", "0010_alter_historicalproject_collection_address_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="historicalproject",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
                verbose_name="管理人",
            ),
        ),
        migrations.AlterField(
            model_name="project",
            name="owner",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="project",
                to=settings.AUTH_USER_MODEL,
                verbose_name="管理人",
            ),
        ),
    ]
