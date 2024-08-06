from celery import shared_task

from analysis.models import DailyFlow
from analysis.models import MonthlyFlow
from analysis.models import WeeklyFlow
from analysis.utils import deposits_flow
from analysis.utils import invoices_flow
from analysis.utils import withdrawals_flow
from common.utils.time import ago


@shared_task
def daily_flow():
    start_at = ago(days=1)

    DailyFlow.objects.create(
        deposits=deposits_flow(start_at),
        invoices=invoices_flow(start_at),
        withdrawals=withdrawals_flow(start_at),
    )


@shared_task
def weekly_flow():
    start_at = ago(days=7)

    WeeklyFlow.objects.create(
        deposits=deposits_flow(start_at),
        invoices=invoices_flow(start_at),
        withdrawals=withdrawals_flow(start_at),
    )


@shared_task
def monthly_flow():
    yesterday = ago(days=1)
    start_at = yesterday.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    MonthlyFlow.objects.create(
        deposits=deposits_flow(start_at),
        invoices=invoices_flow(start_at),
        withdrawals=withdrawals_flow(start_at),
    )
