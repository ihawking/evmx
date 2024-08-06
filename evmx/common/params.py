from dataclasses import dataclass

from web3.types import ChecksumAddress

from chains.models import Chain
from chains.models import TxType
from tokens.models import Token


@dataclass
class SendTokenParams:
    chain: Chain
    token: Token
    to: ChecksumAddress
    value: int
    tx_type: TxType
