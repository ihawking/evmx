import requests
from celery import shared_task

from tokens.models import Token


@shared_task(
    ignore_result=True,
)
def refresh_token_prices():
    token_ids = Token.objects.filter(coingecko_id__isnull=False).values_list(
        "coingecko_id",
        flat=True,
    )

    if not token_ids:
        return

    query_ids = ",".join(token_ids)
    api_url = f"https://api.coingecko.com/api/v3/simple/price?ids={query_ids}&vs_currencies=usd"

    response = requests.get(api_url, timeout=8)
    price_data = response.json()

    for token_id in token_ids:
        current_price = price_data.get(token_id, {}).get("usd", None)

        if current_price is not None:
            token_obj = Token.objects.get(coingecko_id=token_id)
            token_obj.price_in_usd = current_price
            token_obj.save()
