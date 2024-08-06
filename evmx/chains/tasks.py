from celery import shared_task
from django.db import transaction as db_transaction
from django.db.models import Q

from chains.models import Block
from chains.models import Transaction
from chains.models import TransactionQueue
from common.decorators import singleton_task
from common.utils.time import ago


@shared_task(
    ignore_result=True,
    max_retries=None,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
)
@db_transaction.atomic
def filter_and_store_tx(chain_id, block_number, tx_metadata):
    block = Block.objects.select_related("chain").get(
        chain__chain_id=chain_id,
        number=block_number,
    )
    chain = block.chain

    if Transaction.objects.filter(
        hash=tx_metadata["hash"],
        block=block,
    ).exists():
        return

    if chain.is_transaction_should_be_processed(tx_metadata):
        receipt = chain.get_transaction_receipt(tx_hash=tx_metadata["hash"])
        tx = Transaction.objects.create(
            hash=tx_metadata["hash"],
            block=block,
            transaction_index=tx_metadata["transactionIndex"],
            metadata=tx_metadata,
            receipt=receipt,
        )
        tx.initialize()


@shared_task(ignore_result=True)
def transact_the_transaction_queue(pk):
    transaction_queue = TransactionQueue.objects.get(pk=pk)
    transaction_queue.transact()


@shared_task(ignore_result=True)
@singleton_task(timeout=64)
def transact_platform_transactions():
    for transaction_queue in TransactionQueue.objects.filter(
        Q(transacted_at__isnull=True)
        | Q(transacted_at__lt=ago(minutes=16), transaction__isnull=True),
        created_at__lt=ago(seconds=4),
    )[:8]:
        transact_the_transaction_queue.delay(transaction_queue.pk)


@shared_task(
    ignore_result=True,
    max_retries=None,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
)
@db_transaction.atomic
def confirm_the_block(block_pk):
    try:
        block = Block.objects.prefetch_related("transactions").get(pk=block_pk)
    except Block.DoesNotExist:
        return

    if block.confirm_with_transactions():
        return
    else:
        confirm_the_block.apply_async((block_pk,), countdown=4)
