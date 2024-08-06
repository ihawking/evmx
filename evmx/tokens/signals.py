from decimal import Decimal

from django.apps import apps
from django.db.models.signals import post_save

from tokens.models import PlayerTokenValue


def calculate_worth(sender, instance: PlayerTokenValue, created, **kwargs):
    if created:
        instance.worth = instance.token.price_in_usd * Decimal(instance.value)
        instance.save()


def register_calculate_worth():
    for model in apps.get_models():
        if issubclass(model, PlayerTokenValue) and not model.is_abstract_model():
            post_save.connect(calculate_worth, sender=model)
