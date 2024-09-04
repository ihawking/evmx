from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from loguru import logger


def is_empty_project():
    from users.models import User

    return not User.objects.exclude(username="AnonymousUser").exists()


def initialize_group_permissions(group: Group):
    group.permissions.clear()
    try:
        view_project = Permission.objects.get(
            codename="view_project",
        )
        change_project = Permission.objects.get(
            codename="change_project",
        )

        view_block = Permission.objects.get(
            codename="view_block",
        )

        view_transaction = Permission.objects.get(
            codename="view_transaction",
        )

        view_invoice = Permission.objects.get(
            codename="view_invoice",
        )

        view_payment = Permission.objects.get(
            codename="view_payment",
        )

        add_collectionaddressfordiffer = Permission.objects.get(
            codename="add_collectionaddressfordiffer",
        )
        view_collectionaddressfordiffer = Permission.objects.get(
            codename="view_collectionaddressfordiffer",
        )
        change_collectionaddressfordiffer = Permission.objects.get(
            codename="change_collectionaddressfordiffer",
        )
        delete_collectionaddressfordiffer = Permission.objects.get(
            codename="delete_collectionaddressfordiffer",
        )

        view_deposit = Permission.objects.get(
            codename="view_deposit",
        )

        view_withdrawal = Permission.objects.get(
            codename="view_withdrawal",
        )

        view_notification = Permission.objects.get(
            codename="view_notification",
        )

        group.permissions.add(
            view_project,
            change_project,
            view_block,
            view_transaction,
            view_invoice,
            view_payment,
            add_collectionaddressfordiffer,
            delete_collectionaddressfordiffer,
            change_collectionaddressfordiffer,
            view_collectionaddressfordiffer,
            view_deposit,
            view_withdrawal,
            view_notification,
        )
    except Exception as e:
        logger.exception(e)
