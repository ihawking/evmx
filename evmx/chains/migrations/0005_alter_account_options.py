# Generated by Django 4.2.14 on 2024-07-22 08:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("chains", "0004_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="account",
            options={
                "ordering": ("-created_at",),
                "verbose_name": "账户(EVM)",
                "verbose_name_plural": "账户(EVM)",
            },
        ),
    ]
