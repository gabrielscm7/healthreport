import re
from typing import Optional


def validate_cpf(cpf: str) -> bool:
    return bool(re.match(r"^\d{11}$", cpf))


def sanitize_input(text: str) -> str:
    return re.sub(r"[<>&\"']", "", text)


def mask_pii(text: str) -> str:
    if len(text) <= 4:
        return "*" * len(text)
    return text[:2] + "*" * (len(text) - 4) + text[-2:]
