from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from unfold.decorators import display

from common.admin import ReadOnlyModelAdmin
from deposits.models import Deposit


# Register your models here.


@admin.register(Deposit)
class DepositAdmin(ReadOnlyModelAdmin, GuardedModelAdmin):
    list_display = ("project", "player", "chain", "token", "value", "display_status")
    search_fields = ("player__uid", "transaction__hash")
    list_filter = ("token",)

    user_can_access_owned_objects_only = True
    user_owned_objects_field = "project__owner"

    @admin.display(
        description="公链",
    )
    def chain(self, obj):
        return obj.transaction.block.chain

    @display(
        description="状态",
        label={
            "确认中": "info",
            "已确认": "success",
        },
    )
    def display_status(self, instance: Deposit):
        return instance.status
