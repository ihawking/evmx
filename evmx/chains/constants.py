BASE_TRANSFER_GAS = 21_000
ERC20_TRANSFER_GAS = 100_000
DEPLOY_INVOICE_GAS = 160_000

ERC20_TRANSFER_STARTS = "0xa9059cbb"


def gas_limit(*, deploy=False, base=True):
    if deploy:
        return DEPLOY_INVOICE_GAS

    if base:
        return BASE_TRANSFER_GAS

    return ERC20_TRANSFER_GAS
