from typing import Any

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from guardian.admin import GuardedModelAdmin
from unfold.decorators import display
from web3.auto import w3

from common.admin import ModelAdmin
from common.admin import ReadOnlyModelAdmin
from invoices.models import CollectionAddressForDiffer
from invoices.models import Invoice
from invoices.models import Payment


# Register your models here.


class CollectionAddressForDifferForm(forms.ModelForm):
    class Meta:
        model = CollectionAddressForDiffer
        fields = ("address",)

    def clean_address(self):
        from chains.models import Account

        if Account.objects.filter(address=self.cleaned_data["address"]).exists():
            raise ValidationError(_("不能设置为系统内账户"))

        if not w3.is_checksum_address(
            self.cleaned_data["address"],
        ):
            msg = "请输入大小写混合的校验和格式地址"
            raise forms.ValidationError(msg)

        return self.cleaned_data["address"]


@admin.register(CollectionAddressForDiffer)
class CollectionAddressForDifferAdmin(ModelAdmin, GuardedModelAdmin):
    list_display = (
        "project",
        "address",
    )
    form = CollectionAddressForDifferForm
    user_can_access_owned_objects_only = True
    user_owned_objects_field = "project__owner"

    def save_model(
        self,
        request: HttpRequest,
        obj: CollectionAddressForDiffer,
        form: forms.Form,
        change: Any,
    ) -> None:
        if not change:
            if not hasattr(request.user, "project"):
                raise ValidationError(_("本账户无项目"))
            obj.project = request.user.project
        super().save_model(request, obj, form, change)


@admin.register(Invoice)
class InvoiceAdmin(ReadOnlyModelAdmin, GuardedModelAdmin):
    list_display = (
        "project",
        "sys_no",
        "no",
        "type",
        "token",
        "pay_address",
        "value",
        "actual_value",
        "created_at",
        "display_status",
    )
    search_fields = (
        "sys_no",
        "no",
    )
    list_filter = (
        "chain",
        "token",
    )
    user_can_access_owned_objects_only = True
    user_owned_objects_field = "project__owner"

    @display(
        description="状态",
        label={
            "待支付": "warning",
            "确认中": "info",
            "已支付": "success",
            "已失效": "",
        },
    )
    def display_status(self, instance: Invoice):
        return instance.status


@admin.register(Payment)
class PaymentAdmin(ReadOnlyModelAdmin, GuardedModelAdmin):
    list_display = (
        "invoice",
        "token",
        "value_display",
        "transaction",
    )
    user_can_access_owned_objects_only = True
    user_owned_objects_field = "invoice__project__owner"

    @admin.display(
        description="时间",
    )
    def datetime(self, obj: Payment):
        return obj.transaction.datetime

    @admin.display(
        description="代币",
    )
    def token(self, obj):
        return obj.invoice.token

    @admin.display(
        description="支付数量",
    )
    def value_display(self, obj):
        return obj.value_display

    search_fields = ("invoice__no", "invoice__sys_no")
