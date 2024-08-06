# Generated by Django 4.2.14 on 2024-07-27 09:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("globals", "0008_alter_project_owner"),
        ("invoices", "0009_collectionaddressfordiffer"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="collectionaddressfordiffer",
            options={
                "verbose_name": "差额支付地址",
                "verbose_name_plural": "差额支付地址",
            },
        ),
        migrations.AlterField(
            model_name="collectionaddressfordiffer",
            name="project",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                on_delete=django.db.models.deletion.CASCADE,
                to="globals.project",
                verbose_name="项目",
            ),
        ),
    ]