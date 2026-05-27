from __future__ import annotations

import secrets

_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
SHORT_ID_LEN = 8


def short_id() -> str:
    return "".join(_ALPHABET[secrets.randbelow(len(_ALPHABET))] for _ in range(SHORT_ID_LEN))
