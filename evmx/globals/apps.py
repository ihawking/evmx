from django.apps import AppConfig
from django.db.models.signals import post_migrate


class GlobalsProject(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "globals"
    verbose_name = "全局"

    def ready(self):
        from globals import signals

        post_migrate.connect(signals.create_global_project, sender=self)
