from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.db.models import CharField
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from guardian.shortcuts import assign_perm
from chains.models import Account
from globals.models import Project


class User(AbstractUser):
    """
    Default custom user model for EVMx.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]

    @property
    def is_identified(self):
        return not self.is_anonymous and self.username != "AnonymousUser"


@receiver(post_save, sender=User)
def generate_project_while_user_created(sender, instance: User, created, **kwargs):
    if created and instance.is_identified:
        Project.generate(instance)


@receiver(post_save, sender=User)
def join_group_while_user_created(sender, instance: User, created, **kwargs):
    if created and instance.is_identified and not instance.is_superuser:
        group = Group.objects.get(pk=1000)
        instance.groups.add(group)

        instance.is_staff = True
        instance.save()


class Player(models.Model):
    project = models.ForeignKey(
        "globals.Project",
        on_delete=models.CASCADE,
        verbose_name=_("项目"),
    )
    uid = models.CharField(
        max_length=64,
        db_index=True,
        verbose_name=_("玩家UID"),
    )
    deposit_account = models.OneToOneField(
        "chains.Account",
        on_delete=models.CASCADE,
        verbose_name=_("充币地址"),
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="加入时间")

    class Meta:
        unique_together = (("uid", "project"),)
        verbose_name = _("玩家")
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.uid

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        assign_perm("view_player", self.project.owner, self)


@receiver(pre_save, sender=Player)
def add_deposit_account(sender, instance: Player, **kwargs):
    if not instance.deposit_account_id:
        instance.deposit_account_id = Account.generate().id
