from django.contrib import admin
from unfold.admin import TabularInline
from unfold.decorators import display

from common.admin import ModelAdmin
from common.admin import ReadOnlyModelAdmin
from tokens.models import Balance
from tokens.models import Token
from tokens.models import TokenAddress


# Register your models here.
class TokenAddressInline(TabularInline):
    model = TokenAddress
    extra = 0

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_currency:
            return "chain", "address"
        return ()

    def has_add_permission(self, request, obj=None):
        if obj and obj.is_currency:
            return False
        return super().has_add_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_currency:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Token)
class TokenAdmin(ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_currency:
            return "symbol", "decimals"
        return ()

    inlines = (TokenAddressInline,)
    list_display = (
        "symbol",
        "display_type",
        "price_in_usd",
        "decimals",
    )
    exclude = ("chains",)

    @display(
        description="类型",
        label={
            "原生币": "primary",
            "ERC20": "info",
        },
    )
    def display_type(self, instance: Token):
        return instance.get_type_display()


@admin.register(Balance)
class BalanceAdmin(ReadOnlyModelAdmin):
    list_display = (
        "account",
        "chain",
        "token",
        "value_display",
    )
    search_fields = ("account__address",)
    list_filter = ("token",)
