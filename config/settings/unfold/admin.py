from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

UNFOLD = {
    "SITE_TITLE": "EVMx",
    "SITE_HEADER": "EVMx",
    "SITE_URL": "https://evmx.org/",
    "SITE_SYMBOL": "radar",  # symbol from icon set
    "ENVIRONMENT": "common.admin.environment_callback",
    "DASHBOARD_CALLBACK": "common.admin.dashboard_callback",
    "LOGIN": {
        "image": lambda request: static("login-bg.jpg"),
    },
    "SIDEBAR": {
        "navigation": [
            {
                "title": _("系统"),
                "separator": False,  # Top border
                "items": [
                    {
                        "title": _("仪表板"),
                        "icon": "insert_chart",
                        "link": reverse_lazy("admin:index"),
                    },
                    {
                        "title": _("管理员"),
                        "icon": "manage_accounts",
                        "link": reverse_lazy("admin:users_user_changelist"),
                    },
                    {
                        "title": _("项目管理"),
                        "icon": "settings",
                        "link": reverse_lazy("admin:globals_project_changelist"),
                        "badge": "globals.models.status",
                    },
                    {
                        "title": _("任务日志"),
                        "icon": "task",
                        "link": reverse_lazy(
                            "admin:django_celery_results_taskresult_changelist",
                        ),
                    },
                ],
            },
            {
                "title": _("网络"),
                "separator": True,
                "items": [
                    {
                        "title": _("公链"),
                        "icon": "memory",
                        "link": reverse_lazy("admin:chains_chain_changelist"),
                    },
                    {
                        "title": _("区块"),
                        "icon": "deployed_code",
                        "link": reverse_lazy("admin:chains_block_changelist"),
                    },
                    {
                        "title": _("交易"),
                        "icon": "receipt",
                        "link": reverse_lazy("admin:chains_transaction_changelist"),
                    },
                    {
                        "title": _("主动交易"),
                        "icon": "rebase",
                        "link": reverse_lazy(
                            "admin:chains_transactionqueue_changelist",
                        ),
                    },
                ],
            },
            {
                "title": _("代币"),
                "separator": True,
                "items": [
                    {
                        "title": _("代币"),
                        "icon": "paid",
                        "link": reverse_lazy("admin:tokens_token_changelist"),
                    },
                    {
                        "title": _("余额"),
                        "icon": "price_change",
                        "link": reverse_lazy("admin:tokens_balance_changelist"),
                    },
                ],
            },
            {
                "title": _("支付"),
                "separator": True,
                "items": [
                    {
                        "title": _("账单"),
                        "icon": "receipt_long",
                        "link": reverse_lazy("admin:invoices_invoice_changelist"),
                    },
                    {
                        "title": _("付款记录"),
                        "icon": "payments",
                        "link": reverse_lazy("admin:invoices_payment_changelist"),
                    },
                    {
                        "title": _("收款地址"),
                        "icon": "universal_currency",
                        "link": reverse_lazy(
                            "admin:invoices_collectionaddressfordiffer_changelist",
                        ),
                    },
                ],
            },
            {
                "title": _("充提"),
                "separator": True,
                "items": [
                    {
                        "title": _("充币"),
                        "icon": "download",
                        "link": reverse_lazy("admin:deposits_deposit_changelist"),
                    },
                    {
                        "title": _("提币"),
                        "icon": "upload",
                        "link": reverse_lazy("admin:withdrawals_withdrawal_changelist"),
                    },
                ],
            },
            {
                "title": _("通知"),
                "separator": True,
                "items": [
                    {
                        "title": _("通知"),
                        "icon": "notifications_active",
                        "link": reverse_lazy(
                            "admin:notifications_notification_changelist",
                        ),
                    },
                ],
            },
        ],
    },
    "COLORS": {
        "primary": {
            "50": "224 247 247",
            "100": "179 234 234",
            "200": "128 219 221",
            "300": "77 204 208",
            "400": "38 193 197",
            "500": "13 182 187",
            "600": "13 115 119",
            "700": "11 90 94",
            "800": "8 66 68",
            "900": "4 41 41",
        },
    },
}
