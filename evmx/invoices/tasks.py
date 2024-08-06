from celery import shared_task
from django.utils import timezone

from common.decorators import singleton_task
from invoices.models import Invoice
from invoices.models import InvoiceType


@shared_task(ignore_result=True)
@singleton_task(timeout=16)
def gather_invoices():
    for invoice in Invoice.objects.filter(
        type=InvoiceType.Contract,
        paid=True,
        transaction_queue__isnull=True,
        expired_time__lt=timezone.now(),
    ):
        invoice.gather()
