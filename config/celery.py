import os

from celery import Celery
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("evmx")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


app.conf.beat_schedule = {
    "notify": {
        "task": "notifications.tasks.notify",
        "schedule": 1,
    },
    "gather_invoices": {
        "task": "invoices.tasks.gather_invoices",
        "schedule": 1,
    },
    "gather_deposits": {
        "task": "deposits.tasks.gather_deposits",
        "schedule": 8,
    },
    "transact_platform_transactions": {
        "task": "chains.tasks.transact_platform_transactions",
        "schedule": 1,
    },
    "refresh_token_prices": {
        "task": "tokens.tasks.refresh_token_prices",
        "schedule": 120,
    },
    "daily_flow": {
        "task": "analysis.tasks.daily_flow",
        "schedule": crontab(hour="0", minute="0"),
    },
    "weekly_flow": {
        "task": "analysis.tasks.weekly_flow",
        "schedule": crontab(hour="0", minute="0", day_of_week="1"),
    },
    "monthly_flow": {
        "task": "analysis.tasks.monthly_flow",
        "schedule": crontab(hour="0", minute="0", day_of_month="1"),
    },
    "backend_cleanup": {
        "task": "celery.backend_cleanup",
        "schedule": crontab(hour="4", minute="0", day_of_week="1"),
    },
}
