from django.db import models
from django.utils.translation import gettext_lazy as _
from web3.auto import w3

from common.consts import LENGTH_OF_HASH


class ChecksumAddressField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 2 + 40
        kwargs["db_index"] = True

        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname)
        if value and not w3.is_checksum_address(value):
            msg = f"{value} is not a valid checksum address"
            raise ValueError(msg)

        return value


def is_valid_ethereum_256bit_hex_string(s: str) -> bool:
    if len(s) != LENGTH_OF_HASH:
        return False

    if not s.startswith("0x"):
        return False

    hex_digits = set("0123456789abcdefABCDEF")
    return all(c in hex_digits for c in s[2:])


class HexStr64Field(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 2 + 64
        kwargs["unique"] = True
        kwargs["db_index"] = True
        kwargs["verbose_name"] = _("哈希")

        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname)

        if not self.null and not is_valid_ethereum_256bit_hex_string(value):
            msg = f"{value} is not a valid ethereum 256bit hex string"
            raise ValueError(msg)

        return value
