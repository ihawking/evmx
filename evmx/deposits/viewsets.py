from rest_framework import viewsets
from rest_framework.decorators import action as view_action
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from common import http_codes
from common.permissions import RejectAll
from deposits.models import Deposit
from globals.models import Project
from tokens.models import TokenAddress
from users.models import Player


class DepositViewSet(viewsets.ModelViewSet):
    queryset = Deposit.objects.all()

    def get_permissions(self):
        if self.action == "address":
            permission_classes = [AllowAny]
        else:
            permission_classes = [RejectAll]
        return [permission() for permission in permission_classes]

    @view_action(methods=["get"], detail=False)
    def address(self, request: Request):
        appid = request.headers.get("Appid", None)
        project = Project.retrieve(appid=appid)

        uid = request.GET.get("uid", None)
        chain = request.GET.get("chain", None)
        symbol = request.GET.get("symbol", None)

        if not uid:
            return Response(
                status=400,
                data={
                    "error": "UID is required",
                    "code": http_codes.HTTP_400001_INVALID_UID,
                },
            )

        if not TokenAddress.objects.filter(
            chain__chain_id=chain,
            token__symbol=symbol,
            active=True,
        ).exists():
            return Response(
                status=400,
                data={
                    "error": f"{symbol} of chain ID {chain} is not valid",
                    "code": http_codes.HTTP_400002_INVALID_CHAIN_TOKEN,
                },
            )

        player, _ = Player.objects.get_or_create(project=project, uid=uid)

        return Response({"deposit_address": player.deposit_account.address})
