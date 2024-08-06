import re


def is_ethereum_private_key(key: str):
    if not key:
        return False
    pattern = re.compile(r"^[0-9a-fA-F]{64}$")
    return bool(pattern.match(key))
