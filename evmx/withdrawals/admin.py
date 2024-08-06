from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from unfold.decorators import display

from common.admin import ReadOnlyModelAdmin
from withdrawals.models import Withdrawal


# Register your models here.


@admin.register(Withdrawal)
class WithdrawalAdmin(ReadOnlyModelAdmin, GuardedModelAdmin):
    list_display = (
        "project",
        "no",
        "player",
        "to",
        "chain",
        "token",
        "value",
        "display_status",
        "created_at",
    )
    search_fields = (
        "no",
        "player__uid",
    )
    list_filter = ("token",)
    user_can_access_owned_objects_only = True
    user_owned_objects_field = "project__owner"

    @display(
        description="状态",
        label={
            "待提币": "warning",
            "待上链": "warning",
            "确认中": "info",
            "已完成": "success",
        },
    )
    def display_status(self, instance: Withdrawal):
        return instance.status

    @admin.display(
        description="网络",
    )
    def chain(self, obj):
        return obj.transaction_queue.chain.name
