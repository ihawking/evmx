from django.contrib import admin

from analysis.models import DailyFlow
from common.admin import ModelAdmin


# Register your models here.


@admin.register(DailyFlow)
class DailyFlowAdmin(ModelAdmin):
    list_display = (
        "date",
        "invoices",
        "deposits",
        "withdrawals",
    )

    class Meta:
        model = DailyFlow
        fields = "__all__"
