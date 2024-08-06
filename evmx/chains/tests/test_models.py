import pytest

from chains.models import Chain


@pytest.fixture()
def chain(db):
    return Chain.objects.create(
        endpoint_uri="https://data-seed-prebsc-1-s1.binance.org:8545/",
    )


@pytest.fixture()
def latest_block(chain):
    return chain.w3.eth.get_block(chain.get_block_number())


@pytest.fixture()
def latest_transaction_hash(latest_block):
    return latest_block.transactions[-1].hex()


def test_is_transaction_packed(chain):
    assert chain.is_transaction_packed(
        tx_hash="0xd41400c05944d88a1be002bd625b03056ad273fa3d4d7fd90b1f25e8e2c77c6e",
    )


def test_is_transaction_confirmed(chain, latest_transaction_hash):
    assert chain.is_transaction_confirmed(
        tx_hash="0xd41400c05944d88a1be002bd625b03056ad273fa3d4d7fd90b1f25e8e2c77c6e",
    )
    assert not chain.is_transaction_confirmed(tx_hash=latest_transaction_hash)


def test_block_number_consecutive(chain):
    pass
