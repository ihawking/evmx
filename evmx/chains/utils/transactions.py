from typing import NamedTuple

from web3.types import ChecksumAddress

from chains.constants import ERC20_TRANSFER_STARTS
from chains.models import Transaction
from tokens.models import Token
from tokens.models import TokenAddress
from .contract import get_erc20_contract

erc20_contract = get_erc20_contract()


class TokenTransferTuple(NamedTuple):
    token: Token
    from_address: ChecksumAddress
    to_address: ChecksumAddress
    value: int


class TransactionParser:
    def __init__(self, transaction: Transaction) -> None:
        self.chain = transaction.block.chain
        self.metadata = transaction.metadata

    @property
    def token_transfer(self) -> TokenTransferTuple:
        if self.metadata["input"].startswith(ERC20_TRANSFER_STARTS):
            return self._erc20_transfer()
        return self._currency_transfer()

    def _currency_transfer(self) -> TokenTransferTuple:
        return TokenTransferTuple(
            self.chain.currency,
            self.metadata["from"],
            self.metadata["to"],
            self.metadata["value"],
        )

    def _erc20_transfer(self) -> TokenTransferTuple:
        receipt = self.chain.w3.eth.get_transaction_receipt(self.metadata["hash"])
        transfer_event = erc20_contract.events.Transfer().process_receipt(receipt)[0]

        return TokenTransferTuple(
            TokenAddress.objects.get(
                chain=self.chain,
                address=transfer_event["address"],
            ).token,
            transfer_event["args"]["from"],
            transfer_event["args"]["to"],
            transfer_event["args"]["value"],
        )
