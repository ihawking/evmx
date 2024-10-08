# Generated by Django 4.2.14 on 2024-08-02 05:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("analysis", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dailyflow",
            name="deposits",
            field=models.DecimalField(decimal_places=2, max_digits=16),
        ),
        migrations.AlterField(
            model_name="dailyflow",
            name="invoices",
            field=models.DecimalField(decimal_places=2, max_digits=16),
        ),
        migrations.AlterField(
            model_name="dailyflow",
            name="withdrawals",
            field=models.DecimalField(decimal_places=2, max_digits=16),
        ),
        migrations.AlterField(
            model_name="monthlyflow",
            name="deposits",
            field=models.DecimalField(decimal_places=2, max_digits=16),
        ),
        migrations.AlterField(
            model_name="monthlyflow",
            name="invoices",
            field=models.DecimalField(decimal_places=2, max_digits=16),
        ),
        migrations.AlterField(
            model_name="monthlyflow",
            name="withdrawals",
            field=models.DecimalField(decimal_places=2, max_digits=16),
        ),
        migrations.AlterField(
            model_name="weeklyflow",
            name="deposits",
            field=models.DecimalField(decimal_places=2, max_digits=16),
        ),
        migrations.AlterField(
            model_name="weeklyflow",
            name="invoices",
            field=models.DecimalField(decimal_places=2, max_digits=16),
        ),
        migrations.AlterField(
            model_name="weeklyflow",
            name="withdrawals",
            field=models.DecimalField(decimal_places=2, max_digits=16),
        ),
    ]
