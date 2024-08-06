import json
from pathlib import Path

from django.conf import settings

from common.decorators import cache_func


def chain_icon_url(chain_id):
    slugs_path = Path(settings.BASE_DIR) / "evmx" / "chains" / "data" / "slugs.json"

    with slugs_path.open(encoding="utf-8") as file:
        slugs_data = json.load(file)

    slug = slugs_data.get(str(chain_id), None)

    return f"https://icons.llamao.fi/icons/chains/rsz_{slug}.jpg" if slug else None


def chain_metadata(chain_id):
    # 指定JSON文件的路径
    file_path = Path(settings.BASE_DIR) / "evmx" / "chains" / "data" / "chains.json"

    # 打开并读取JSON文件
    with file_path.open(encoding="utf-8") as file:
        chains = json.load(file)

    for chain in chains:
        if chain["chainId"] == chain_id:
            return {
                "name": chain["name"],
                "symbol": chain["chain"],
                "currency": {
                    "name": chain["nativeCurrency"]["name"],
                    "symbol": chain["nativeCurrency"]["symbol"],
                    "decimals": chain["nativeCurrency"]["decimals"],
                },
            }
    return None


@cache_func(timeout=8, use_params=True)
def abi(erc=20):
    abi_path = (
        Path(settings.BASE_DIR) / "evmx" / "chains" / "data" / f"erc{erc}_abi.json"
    )

    with abi_path.open(mode="r") as f:
        return json.load(f)


@cache_func(timeout=8, use_params=True)
def invoice_contract(*, eth: bool):
    file_name = "eth_invoice.txt" if eth else "erc20_invoice.txt"
    contract_path = Path(settings.BASE_DIR) / "evmx" / "chains" / "data" / file_name

    with contract_path.open(mode="r") as f:
        return f.read().replace("\n", "")


if __name__ == "__main__":
    pass
