from decimal import Decimal

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.serializers import Serializer

from chains.models import Chain
from chains.serializers import ChainSerializer
from chains.utils.create2 import is_chain_valid
from common.consts import MAX_INVOICE_DURATION
from common.consts import MIN_INVOICE_DURATION
from globals.models import Project
from invoices.models import Invoice
from invoices.models import InvoiceType
from invoices.models import Payment
from tokens.models import Token


class InvoiceCreateSerializer(Serializer):
    type = serializers.CharField(default=InvoiceType.Differ)
    no = serializers.CharField(required=True)
    subject = serializers.CharField(max_length=64)
    detail = serializers.JSONField(default=dict)
    token = serializers.CharField(required=True)
    chain = serializers.CharField(required=True)
    value = serializers.DecimalField(
        required=True,
        max_digits=36,
        decimal_places=18,
    )
    differ_step = serializers.DecimalField(
        max_digits=36,
        decimal_places=18,
        default=Decimal(0),
    )
    differ_max = serializers.DecimalField(
        max_digits=36,
        decimal_places=18,
        default=Decimal(0),
    )
    duration = serializers.IntegerField(default=10)

    def validate_type(self, value):
        if value not in InvoiceType:
            raise serializers.ValidationError(_("账单类型错误."))
        return value

    def validate_token(self, value):
        if not Token.objects.filter(symbol=value).exists():
            raise serializers.ValidationError(_("代币未创建."))
        return value

    def validate_chain(self, value):
        if not Chain.objects.filter(chain_id=value, active=True).exists():
            raise serializers.ValidationError(_("网络不可用."))
        return value

    @staticmethod
    def _is_chain_token_supported(attrs) -> bool:
        chain = Chain.objects.get(chain_id=attrs["chain"])
        token = Token.objects.get(symbol=attrs["token"])

        return token.support_this_chain(chain)

    @staticmethod
    def _is_differ_valid(attrs) -> bool:
        return Decimal(0) < attrs["differ_step"] <= attrs["differ_max"]

    def validate(self, attrs):
        request = self.context.get("request")
        project = Project.retrieve(appid=request.headers.get("Appid", None))

        if not self._is_chain_token_supported(attrs):
            msg = _("网络与代币不匹配.")
            raise serializers.ValidationError(msg)

        if attrs["type"] == InvoiceType.Contract and not is_chain_valid(attrs["chain"]):
            msg = _("此链不支持合约账单.")
            raise serializers.ValidationError(msg)

        if attrs["type"] == InvoiceType.Differ and not self._is_differ_valid(attrs):
            msg = _("差额数值设置错误.")
            raise serializers.ValidationError(msg)

        if (
            attrs["duration"] < MIN_INVOICE_DURATION
            or attrs["duration"] > MAX_INVOICE_DURATION
        ):
            msg = _("支付时间需要介于5分钟-2小时.")
            raise serializers.ValidationError(msg)

        if Invoice.objects.filter(project=project, no=attrs["no"]).exists():
            msg = _("商户单号重复.")
            raise serializers.ValidationError(msg)

        return attrs


class InvoiceSerializer(serializers.ModelSerializer):
    chain = ChainSerializer(read_only=True)
    pay_url = serializers.SerializerMethodField(default="")

    def get_pay_url(self, obj: Invoice):
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.sys_no)
        return None

    class Meta:
        model = Invoice
        fields = (
            "sys_no",
            "no",
            "subject",
            "detail",
            "chain",
            "token_symbol",
            "token_address",
            "pay_address",
            "value",
            "pay_url",
            "redirect_url",
        )


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("tx_hash", "value_display", "confirm_process")
