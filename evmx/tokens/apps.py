from django.apps import AppConfig


class TokensConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tokens"
    verbose_name = "代币"

    def ready(self):
        from tokens.signals import register_calculate_worth

        register_calculate_worth()
