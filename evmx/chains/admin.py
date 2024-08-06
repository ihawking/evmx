from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from guardian.admin import GuardedModelAdmin
from unfold.admin import TabularInline
from unfold.decorators import display
from web3 import Web3

from chains.models import Account
from chains.models import Block
from chains.models import Chain
from chains.models import Transaction
from chains.models import TransactionQueue
from common.admin import ModelAdmin
from common.admin import ReadOnlyModelAdmin
from tokens.models import Balance


# Register your models here.


class ChainForm(forms.ModelForm):
    class Meta:
        model = Chain
        fields = (
            "endpoint_uri",
            "name",
            "chain_id",
            "block_confirmations_count",
            "currency",
            "active",
        )

    def clean_endpoint_uri(self):
        endpoint_uri = self.cleaned_data["endpoint_uri"]
        instance: Chain = self.instance
        chain_id = Web3(Web3.HTTPProvider(endpoint_uri)).eth.chain_id

        if (
            not instance.chain_id and Chain.objects.filter(pk=chain_id).exists()
        ):  # 如果是新建 Chain,需要验证是否与已存在的公链重复
            msg = "公链重复"
            raise forms.ValidationError(msg)

        if (
            instance.chain_id and chain_id != instance.chain_id
        ):  # 验证表单中的 uri 指向的 chain id,是否和数据库中的数据匹配
            msg = "RPC 地址与当前 Chain ID 不匹配"
            raise forms.ValidationError(msg)
        return endpoint_uri


@admin.register(Chain)
class ChainAdmin(ModelAdmin):
    form = ChainForm
    readonly_fields = ("name", "chain_id", "currency")
    list_display = (
        "display_header",
        "display_chain_id",
        "currency",
        "endpoint_uri",
        "active",
    )
    list_editable = ("active",)

    @display(description="Chain ID", label=True)
    def display_chain_id(self, instance: Chain):
        return instance.chain_id

    @display(description="名称", header=True)
    def display_header(self, instance: Chain):
        return [
            instance.name,
            None,
            instance.chain_id,
            {
                "path": instance.icon,
            },
        ]

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.add_fieldsets
        return self.edit_fieldsets

    add_fieldsets = (
        (
            "节点",
            {"fields": ("endpoint_uri",)},
        ),
    )

    edit_fieldsets = (
        (
            "节点",
            {"fields": ("endpoint_uri",)},
        ),
        ("公链信息", {"fields": ("name", "chain_id", "currency")}),
        (
            "配置",
            {"fields": ("block_confirmations_count", "active")},
        ),
    )


@admin.register(Block)
class BlockAdmin(ReadOnlyModelAdmin):
    list_filter = ("chain", "confirmed")
    search_fields = ("hash", "number")
    list_display = ("chain", "display_number", "hash", "display_status")
    ordering = ("-id",)

    @display(description="区块号", label=True)
    def display_number(self, instance: Block):
        return instance.number

    @display(
        description="状态",
        label={
            "已确认": "success",
            "确认中": "info",
        },
    )
    def display_status(self, instance: Block):
        return instance.status


@admin.register(Transaction)
class TransactionAdmin(ReadOnlyModelAdmin, GuardedModelAdmin):
    ordering = ("-id",)
    list_filter = (
        "block__chain",
        "type",
    )
    search_fields = (
        "hash",
        "block__number",
    )
    list_display = (
        "hash",
        "block",
        "datetime",
        "display_type",
        "display_status",
    )
    user_can_access_owned_objects_only = True
    user_owned_objects_field = "project__owner"

    @display(
        description="状态",
        label={
            "已确认": "success",
            "确认中": "info",
        },
    )
    def display_status(self, instance: Transaction):
        return instance.block.status

    @display(description="类型", label=False)
    def display_type(self, instance: Transaction):
        return instance.get_type_display()


# Register your models here.
class BalanceInline(TabularInline):
    model = Balance
    extra = 0
    readonly_fields = ("value_display",)

    @admin.display(
        description=_("数量(小数)"),
    )
    def value_display(self, instance):
        return instance.value_display

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Account)
class AccountAdmin(ReadOnlyModelAdmin):
    inlines = [BalanceInline]
    list_display = ("address", "type")
    search_fields = ("address",)


@admin.register(TransactionQueue)
class TransactionQueueAdmin(ReadOnlyModelAdmin):
    ordering = ("-created_at",)
    list_display = (
        "account",
        "chain",
        "type",
        "nonce",
        "display_status",
        "formatted_created_at",
        "formatted_transacted_at",
    )
    search_fields = ("hash", "account__address")

    @admin.display(
        description="创建时间",
        ordering="created_at",
    )
    def formatted_created_at(self, obj):
        return obj.created_at.strftime("%-m月%-d日 %H:%M:%S")

    @admin.display(
        description="执行时间",
        ordering="transacted_at",
    )
    def formatted_transacted_at(self, obj):
        if obj.transacted_at:
            return obj.transacted_at.strftime("%-m月%-d日 %H:%M:%S")
        return None

    @display(
        description="状态",
        label={
            "待执行": "",
            "待上链": "warning",
            "确认中": "info",
            "已确认": "success",
        },
    )
    def display_status(self, instance: TransactionQueue):
        return instance.status
