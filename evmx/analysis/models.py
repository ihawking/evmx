from datetime import timedelta

from django.db import models
from django.db.models import Max
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


# Create your models here.


class Flow(models.Model):
    invoices = models.DecimalField(max_digits=16, decimal_places=2)
    deposits = models.DecimalField(max_digits=16, decimal_places=2)
    withdrawals = models.DecimalField(max_digits=16, decimal_places=2)

    date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        abstract = True

    def __str__(self):
        return str(self.date)

    @property
    def day(self):
        return self.date.day

    @property
    def inflow(self):
        return self.invoices + self.deposits

    @property
    def outflow(self):
        return self.withdrawals


class DailyFlow(Flow):
    def __str__(self):
        return str(self.date)

    @classmethod
    def get_recent_flows(cls):
        from analysis.serializers import DailyFlowSerializer

        # 获取数据库中最新的日期
        latest_date = cls.objects.aggregate(Max("date"))["date__max"]

        if not latest_date:
            # 如果数据库为空,则使用当前日期
            latest_date = timezone.now().date() - timedelta(days=1)

        # 计算30天前的日期
        start_date = latest_date - timedelta(days=29)

        # 获取最近30天的记录,按日期排序
        recent_flows = list(cls.objects.filter(date__gte=start_date).order_by("date"))

        # 获取已有的日期
        existing_dates = [flow.date for flow in recent_flows]

        # 生成所需的日期列表
        required_dates = [start_date + timedelta(days=i) for i in range(30)]

        # 补齐缺失的日期
        recent_flows.extend(
            cls(date=date, invoices=0, deposits=0, withdrawals=0)
            for date in required_dates
            if date not in existing_dates
        )

        # 按日期重新排序
        recent_flows.sort(key=lambda x: x.date)
        return [DailyFlowSerializer(flow).data for flow in recent_flows]


@receiver(post_save, sender=DailyFlow)
def fill_date(sender, instance: DailyFlow, created, **kwargs):
    if created:
        instance.date = instance.created_at.date() - timedelta(days=1)
        instance.save()


class MonthlyFlow(Flow):
    pass


class WeeklyFlow(Flow):
    pass
