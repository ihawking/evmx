from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django_celery_results.models import TaskResult
from guardian.admin import GuardedModelAdmin
from web3.auto import w3 as w3_auto

from chains.models import Account
from common.admin import ModelAdmin
from globals.models import Project

admin.site.unregister(TaskResult)


# Register your models here.
class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = (
            "collection_address",
            "ip_white_list",
        )

    def clean_collection_address(self):
        collection_address = self.cleaned_data.get("collection_address")

        if Account.objects.filter(address=collection_address).exists():
            msg = _("归集地址不能设置为平台内部账户地址")
            raise forms.ValidationError(msg)

        if not w3_auto.is_checksum_address(
            collection_address,
        ):  # 验证表单中的 uri 指向的 chain id,是否和数据库中的数据匹配
            msg = _("请输入大小写混合的校验和格式地址")
            raise forms.ValidationError(msg)
        return collection_address

    def clean_ip_white_list(self):
        """
        检查设置的白名单IP 地址或网络是否合法
        :return: None
        """
        ip_white_list = self.cleaned_data.get("ip_white_list")

        from common.utils.security import is_ip_or_network

        if not all(is_ip_or_network(addr) for addr in ip_white_list.split(",")):
            raise forms.ValidationError(_("IP 白名单格式错误."))
        return ip_white_list


@admin.register(Project)
class ProjectAdmin(
    ModelAdmin,
    GuardedModelAdmin,
):
    form = ProjectForm
    list_display = (
        "name",
        "appid",
        "system_account",
        "collection_address",
        "webhook",
        "active",
    )
    list_editable = ("active",)

    user_can_access_owned_objects_only = True
    user_owned_objects_field = "owner"

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm("change_project", obj)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # 修改项目
            return (
                "system_account",
                "appid",
                "owner",
            )
        # 新建项目
        return (
            "system_account",
            "appid",
        )

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.add_fieldsets
        return self.edit_fieldsets

    add_fieldsets = (
        (
            "基本",
            {
                "fields": (
                    "owner",
                    "name",
                    "webhook",
                    "pre_notify",
                ),
            },
        ),
        ("安全", {"fields": ("ip_white_list",)}),
        (
            "资金",
            {
                "fields": ("collection_address",),
            },
        ),
    )
    edit_fieldsets = (
        (
            "基本",
            {
                "fields": (
                    "name",
                    "appid",
                    "webhook",
                    "pre_notify",
                    "owner",
                ),
            },
        ),
        (
            "安全",
            {
                "fields": (
                    "hmac_key",
                    "ip_white_list",
                ),
            },
        ),
        (
            "资金",
            {
                "fields": (
                    "collection_address",
                    "system_account",
                    "gather_worth",
                    "gather_time",
                    "minimal_gather_worth",
                ),
            },
        ),
    )

    def has_delete_permission(self, request, obj=None):
        return False  # 禁止删除


@admin.register(TaskResult)
class TaskResultAdmin(ModelAdmin):
    list_display = ("task_id", "task_name", "status", "date_done")
    list_filter = ("status", "task_name", "date_done")
