from django.db.models import Sum

from common.decorators import cache_func
from deposits.models import Deposit
from invoices.models import Invoice
from withdrawals.models import Withdrawal


@cache_func(timeout=8, use_params=True)
def deposits_flow(start_at):
    deposits = Deposit.objects.filter(created_at__gte=start_at)
    return deposits.aggregate(Sum("worth"))["worth__sum"] or 0


@cache_func(timeout=8, use_params=True)
def withdrawals_flow(start_at):
    withdrawals = Withdrawal.objects.filter(
        created_at__gte=start_at,
        transaction_queue__transaction__isnull=False,
    )
    return withdrawals.aggregate(Sum("worth"))["worth__sum"] or 0


@cache_func(timeout=8, use_params=True)
def invoices_flow(start_at):
    invoices = Invoice.objects.filter(created_at__gte=start_at, paid=True)
    return invoices.aggregate(Sum("worth"))["worth__sum"] or 0


@cache_func(timeout=8, use_params=True)
def flow(start_at):
    inflow = 0
    outflow = 0

    inflow += deposits_flow(start_at)
    inflow += invoices_flow(start_at)

    outflow += withdrawals_flow(start_at)

    return inflow, outflow
