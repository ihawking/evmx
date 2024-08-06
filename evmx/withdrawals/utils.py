import eth_abi
from web3.types import ChecksumAddress
from web3.types import HexStr

from chains.constants import ERC20_TRANSFER_STARTS


def generate_data(to: ChecksumAddress, value: int) -> HexStr:
    encoded_params = eth_abi.encode(
        ["address", "uint256"],
        [
            to,
            value,
        ],
    )

    return ERC20_TRANSFER_STARTS + encoded_params.hex()
