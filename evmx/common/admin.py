import json

from django.utils import timezone
from django.views.generic import RedirectView
from unfold.admin import ModelAdmin

from analysis.utils import deposits_flow
from analysis.utils import invoices_flow
from analysis.utils import withdrawals_flow

today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)


class HomeView(RedirectView):
    pattern_name = "admin:index"


def environment_callback(request):
    return ["版本: 1.0.1", "info"]


class NoDeleteModelAdmin(ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False  # 禁止删除


class ReadOnlyModelAdmin(ModelAdmin):
    def has_change_permission(self, request, obj=None):
        return False  # 禁止编辑

    def has_delete_permission(self, request, obj=None):
        return False  # 禁止删除

    def has_add_permission(self, request):
        return False  # 禁止添加


def dashboard_callback(request, context):
    from analysis.models import DailyFlow
    from chains.models import Transaction

    latest_30_daily_flow = DailyFlow.get_recent_flows()

    positive = [_["deposits"] for _ in latest_30_daily_flow]
    negative = [-_["withdrawals"] for _ in latest_30_daily_flow]
    average = [_["invoices"] for _ in latest_30_daily_flow]

    performance_positive = [_["inflow"] for _ in latest_30_daily_flow]
    performance_negative = [_["outflow"] for _ in latest_30_daily_flow]

    txs = Transaction.objects.all()[:10]
    txs = [
        {
            "title": tx.hash,
            "description": tx.get_type_display(),
            "value": tx.confirm_process,
        }
        for tx in txs
    ]

    context.update(
        {
            "kpi": [
                {
                    "title": "账单收款",
                    "metric": f"${invoices_flow(today)}",
                    "chart": json.dumps(
                        {
                            "labels": [_["day"] for _ in latest_30_daily_flow],
                            "datasets": [{"data": average, "borderColor": "#9333ea"}],
                        },
                    ),
                },
                {
                    "title": "充币总额",
                    "metric": f"${deposits_flow(today)}",
                },
                {
                    "title": "提币总额",
                    "metric": f"${withdrawals_flow(today)}",
                },
            ],
            "progress": txs,
            "chart": json.dumps(
                {
                    "labels": [f'{_["day"]}日' for _ in latest_30_daily_flow],
                    "datasets": [
                        {
                            "label": "账单收款",
                            "type": "line",
                            "data": average,
                            "backgroundColor": "#f0abfc",
                            "borderColor": "#f0abfc",
                        },
                        {
                            "label": "充币",
                            "data": positive,
                            "backgroundColor": "#9333ea",
                        },
                        {
                            "label": "提币",
                            "data": negative,
                            "backgroundColor": "#f43f5e",
                        },
                    ],
                },
            ),
            "performance": [
                {
                    "title": "小计流入",
                    "metric": f"${sum(performance_positive)}",
                    "chart": json.dumps(
                        {
                            "labels": [_["day"] for _ in latest_30_daily_flow],
                            "datasets": [
                                {
                                    "data": performance_positive,
                                    "borderColor": "#9333ea",
                                },
                            ],
                        },
                    ),
                },
                {
                    "title": "小计流出",
                    "metric": f"${sum(performance_negative)}",
                    "chart": json.dumps(
                        {
                            "labels": [_["day"] for _ in latest_30_daily_flow],
                            "datasets": [
                                {
                                    "data": performance_negative,
                                    "borderColor": "#f43f5e",
                                },
                            ],
                        },
                    ),
                },
            ],
        },
    )

    return context
