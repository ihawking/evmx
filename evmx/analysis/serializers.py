from decimal import Decimal

from rest_framework import serializers

from analysis.models import DailyFlow


class DecimalToFloatField(serializers.Field):
    def to_representation(self, value):
        # 将 Decimal 转换为 float
        return float(value)

    def to_internal_value(self, data):
        # 将输入数据转换为 Decimal
        try:
            return Decimal(data)
        except (TypeError, ValueError) as e:
            msg = "Invalid decimal value"
            raise serializers.ValidationError(msg) from e


class DailyFlowSerializer(serializers.ModelSerializer):
    invoices = DecimalToFloatField()
    deposits = DecimalToFloatField()
    withdrawals = DecimalToFloatField()
    inflow = DecimalToFloatField()
    outflow = DecimalToFloatField()

    class Meta:
        model = DailyFlow
        fields = ("invoices", "deposits", "withdrawals", "inflow", "outflow", "day")
