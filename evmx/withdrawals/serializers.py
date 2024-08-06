from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.serializers import Serializer
from web3.auto import w3 as auto_w3

from chains.models import Account
from chains.models import Chain
from chains.utils.contract import get_erc20_contract
from globals.models import Project
from tokens.models import Token
from tokens.models import TokenAddress
from withdrawals.models import Withdrawal


class CreateWithdrawalSerializer(Serializer):
    no = serializers.CharField(required=True)
    to = serializers.CharField(required=True)
    symbol = serializers.CharField(required=True)
    chain = serializers.CharField(required=True)
    value = serializers.DecimalField(required=True, max_digits=36, decimal_places=18)

    def validate_no(self, value):
        request = self.context.get("request")
        project = Project.retrieve(appid=request.headers.get("Appid", None))

        if Withdrawal.objects.filter(project=project, no=value).exists():
            raise serializers.ValidationError(_("商户单号重复."))
        return value

    def validate_to(self, value):
        if not auto_w3.is_checksum_address(value):
            raise serializers.ValidationError(_("请输入合法的校验和地址."))
        if Account.objects.filter(address=value).exists():
            raise serializers.ValidationError(_("无法提现到平台内地址."))
        return value

    def validate_symbol(self, value):
        if not Token.objects.filter(symbol=value).exists():
            msg = _("代币未创建.")
            raise serializers.ValidationError(msg)
        return value

    def validate_chain(self, value):
        msg = _("网络 %s 不可用.") % value
        if not Chain.objects.filter(chain_id=value, active=True).exists():
            raise serializers.ValidationError(msg)
        return value

    @staticmethod
    def _is_chain_token_supported(attrs) -> bool:
        chain = Chain.objects.get(chain_id=attrs["chain"])
        token = Token.objects.get(symbol=attrs["symbol"])

        return token.support_this_chain(chain)

    @staticmethod
    def _is_contract_address(attrs) -> bool:
        chain = Chain.objects.get(chain_id=attrs["chain"])

        return chain.is_contract(attrs["to"])

    def _is_balance_enough(self, attrs) -> bool:
        request = self.context.get("request")

        project = Project.retrieve(appid=request.headers.get("Appid", None))

        chain = Chain.objects.get(chain_id=attrs["chain"])
        token = Token.objects.get(symbol=attrs["symbol"])

        value_on_chain = attrs["value"] * 10**token.decimals

        if chain.currency == token:
            return chain.get_balance(address=project.system_address) >= value_on_chain

        chain_token = TokenAddress.objects.get(chain=chain, token=token)
        erc20_contract = get_erc20_contract(
            address=chain_token.address,
            w3=chain.w3,
        )
        return (
            erc20_contract.functions.balanceOf(project.system_address).call()
            >= value_on_chain
        )

    def validate(self, attrs):
        if not self._is_chain_token_supported(attrs):
            raise serializers.ValidationError(
                _("网络 %(chain)s 不支持代币 %(symbol)s.")
                % {"chain": attrs["chain"], "symbol": attrs["symbol"]},
            )

        if not self._is_balance_enough(attrs):
            msg = _("系统账户中 %s 余额不足.") % attrs["symbol"]
            raise serializers.ValidationError(msg)

        if self._is_contract_address(attrs):
            msg = _("收币地址不可以为合约地址.")
            raise serializers.ValidationError(msg)

        return attrs
