from django.db import transaction as db_tx
from django.http.response import HttpResponse
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from chains.models import Chain
from chains.models import TxType
from common.permissions import RejectAll
from globals.models import Project
from tokens.models import Token
from withdrawals.models import Withdrawal
from withdrawals.serializers import CreateWithdrawalSerializer


class WithdrawalViewSet(viewsets.ModelViewSet):
    queryset = Withdrawal.objects.all()

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [AllowAny]
        else:
            permission_classes = [RejectAll]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        serializer = CreateWithdrawalSerializer(
            data=request.data,
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        validated_data = serializer.validated_data

        project = Project.retrieve(appid=request.headers.get("Appid", None))

        chain = Chain.objects.get(chain_id=validated_data["chain"])
        token = Token.objects.get(symbol=validated_data["symbol"])

        value = validated_data["value"]

        account = project.system_account

        with db_tx.atomic():
            transaction_queue = account.send_token(
                chain=chain,
                token=token,
                to=validated_data["to"],
                value=int(value * 10**token.decimals),
                tx_type=TxType.Withdrawal,
            )
            Withdrawal.objects.create(
                project=project,
                no=validated_data["no"],
                to=validated_data["to"],
                value=value,
                token=token,
                transaction_queue=transaction_queue,
            )

        return HttpResponse("ok")
