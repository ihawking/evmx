import os
from datetime import timedelta

import eth_abi
from django.db import transaction as db_transaction
from django.utils import timezone
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from web3.types import HexStr

from chains.models import Chain
from chains.utils import create2
from chains.utils import invoice_contract
from common import http_codes
from common.permissions import RejectAll
from common.utils.crypto import generate_random_code
from globals.models import Project
from invoices.models import Invoice
from invoices.models import InvoiceType
from invoices.serializers import InvoiceCreateSerializer
from invoices.serializers import InvoiceSerializer
from tokens.models import Token


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [AllowAny]
        else:
            permission_classes = [RejectAll]
        return [permission() for permission in permission_classes]

    @staticmethod
    def get_init_code(chain: Chain, token: Token, project: Project):
        if chain.currency == token:
            constructor_arguments = [project.collection_address]
            encoded_arguments = eth_abi.encode(["address"], constructor_arguments)
            init_code = invoice_contract(eth=True) + encoded_arguments.hex()
        else:
            constructor_arguments = [token.address(chain), project.collection_address]
            encoded_arguments = eth_abi.encode(
                ["address", "address"],
                constructor_arguments,
            )
            init_code = invoice_contract(eth=False) + encoded_arguments.hex()

        return init_code

    def create(self, request, *args, **kwargs):
        serializer = InvoiceCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        validated_data = serializer.validated_data

        project = Project.retrieve(appid=request.headers.get("Appid", None))
        token = Token.objects.get(symbol=validated_data["token"])
        chain = Chain.objects.get(chain_id=validated_data["chain"])

        with db_transaction.atomic():
            if validated_data["type"] == InvoiceType.Differ:
                salt = None
                init_code = None
                pay_address, value = Invoice.get_differ(
                    project,
                    validated_data["value"],
                    validated_data["differ_step"],
                    validated_data["differ_max"],
                )
                collection_address = pay_address
                original_value = validated_data["value"]

                if not pay_address:
                    return Response(
                        status=400,
                        data={
                            "error": "Differ is not enough.",
                            "code": http_codes.HTTP_400006_INVOICE_DIFFER_NOT_ENOUGH,
                        },
                    )
            else:
                salt = os.urandom(32).hex()
                init_code = self.get_init_code(chain, token, project)
                pay_address = create2.predict_address(HexStr(salt), init_code)
                value = validated_data["value"]
                collection_address = project.collection_address
                original_value = None

            invoice = Invoice.objects.create(
                project=project,
                type=validated_data["type"],
                sys_no=f"EI-{generate_random_code(length=16, readable=True)}",
                no=validated_data["no"],
                subject=validated_data["subject"],
                detail=validated_data["detail"],
                token=token,
                chain=chain,
                value=value,
                original_value=original_value,
                expired_time=timezone.now()
                + timedelta(minutes=validated_data["duration"]),
                salt=salt,
                init_code=init_code,
                pay_address=pay_address,
                collection_address=collection_address,
            )

            serializer_context = {
                "request": request,
            }
            return Response(
                InvoiceSerializer(invoice, context=serializer_context).data,
                status=status.HTTP_200_OK,
            )
