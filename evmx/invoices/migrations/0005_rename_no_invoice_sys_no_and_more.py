# Generated by Django 4.2.14 on 2024-07-25 14:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("invoices", "0004_invoice_expired_invoice_original_value_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="invoice",
            old_name="no",
            new_name="sys_no",
        ),
        migrations.AlterField(
            model_name="invoice",
            name="original_value",
            field=models.DecimalField(
                blank=True,
                decimal_places=8,
                help_text="当类型为Differ的时候,最初的期望应付数量",
                max_digits=32,
                null=True,
                verbose_name="原应付数量",
            ),
        ),
    ]