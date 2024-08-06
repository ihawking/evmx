from celery import shared_task
from django.db.models import Q

from chains.models import Account
from chains.models import Chain
from common.decorators import singleton_task
from common.utils.time import ago
from globals.models import Project
from tokens.models import Balance
from tokens.models import Token


@shared_task(
    ignore_result=True,
)
@singleton_task(timeout=64)
def gather_deposits():
    chains = list(Chain.objects.all())
    tokens = list(Token.objects.all())
    projects = list(Project.objects.all())

    for project in projects:
        for chain in chains:
            gather_time_ago = ago(
                seconds=chain.block_confirmations_count * chain.block_mining_time * 2,
            )

            for token in tokens:
                account_ids = Balance.objects.filter(
                    Q(value__gte=token.gather_value(project))
                    | Q(
                        last_gathered_at__lte=ago(days=project.gather_time),
                        value__gte=token.minimal_gather_value(project),
                    ),
                    last_gathered_at__lte=gather_time_ago,
                    account__player__project=project,
                    chain=chain,
                    token=token,
                ).values_list("account", flat=True)[:8]

                accounts = Account.objects.filter(id__in=account_ids)

                for account in accounts:
                    account.gather(chain, token)
