# Generated by Django 4.2.14 on 2024-07-27 07:47

import django.db.models.deletion
from django.db import migrations, models

import common.fields


class Migration(migrations.Migration):

    dependencies = [
        ("globals", "0007_alter_historicalproject_name_alter_project_name"),
        ("invoices", "0008_alter_invoice_actual_value_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="CollectionAddressForDiffer",
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
                        db_index=True, max_length=42, unique=True
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="globals.project",
                        verbose_name="项目",
                    ),
                ),
            ],
            options={
                "verbose_name": "差额专用支付地址",
                "verbose_name_plural": "差额专用支付地址",
            },
        ),
    ]
