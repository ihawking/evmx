from web3.auto import w3 as auto_w3

from chains.utils import abi


def get_erc20_contract(address=None, w3=auto_w3):
    return w3.eth.contract(address=address, abi=abi(20))
