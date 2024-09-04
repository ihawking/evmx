from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db import transaction as db_transaction
from django.utils.translation import gettext_lazy as _

from globals.utils import initialize_group_permissions, is_empty_project
from users.models import User


@db_transaction.atomic
def create_global_project():
    if is_empty_project():
        admin = User.objects.create(
            username="admin",
            is_superuser=True,
            is_staff=True,
        )
        admin.set_password("admin")
        admin.save()

    try:
        manager_group = Group.objects.get(pk=1000)
    except Group.DoesNotExist:
        manager_group = Group.objects.create(pk=1000, name=_("项目管理员组"))

    initialize_group_permissions(manager_group)


class Command(BaseCommand):
    help = "初始化项目,创建超级用户与管理员组"

    def handle(self, *args, **options):
        create_global_project()
