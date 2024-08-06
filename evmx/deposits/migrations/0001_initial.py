# Generated by Django 4.2.14 on 2024-07-21 06:41

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Deposit",
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
                    "value",
                    models.DecimalField(
                        decimal_places=8, max_digits=32, verbose_name="数量"
                    ),
                ),
                (
                    "worth",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=32,
                        verbose_name="价值(USD)",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "充币",
                "verbose_name_plural": "充币",
            },
        ),
    ]