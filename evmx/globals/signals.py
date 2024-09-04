from django.contrib.auth.models import Group
from django.db import transaction as db_transaction
from django.utils.translation import gettext_lazy as _
from loguru import logger

from chains.models import Account
from common.utils.crypto import generate_random_code
from globals.models import Project
from globals.utils import initialize_group_permissions
from users.models import User


@db_transaction.atomic
def create_global_project(sender, **kwargs):
    try:
        Project.objects.get(id=1)

    except Project.DoesNotExist:
        admin = User.objects.create(
            username="admin",
            is_superuser=True,
            is_staff=True,
        )
        passwd = "admin"
        admin.set_password(passwd)
        admin.save()

        logger.warning(
            _(
                "初始化超级用户成功;账户:admin;密码:admin;请务必登录后台修改密码",
            ).format(passwd=passwd),
        )

        Project.objects.create(
            id=1,
            owner=admin,
            name=_("默认项目"),
            appid=f"EVMx-{generate_random_code(length=16, readable=True)}",
            system_account=Account.generate(),
            hmac_key=generate_random_code(length=32),
        )

    try:
        group = Group.objects.get(pk=1)

    except Group.DoesNotExist:
        group = Group.objects.create(pk=1, name=_("项目管理员组"))

    initialize_group_permissions(group)
