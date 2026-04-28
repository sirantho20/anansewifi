import secrets

VOUCHER_CODE_LENGTH = 6
# Uppercase A–Z and digits 0–9 (stored codes are uppercase by default).
VOUCHER_CODE_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def normalize_voucher_code(raw: str) -> str:
    return (raw or "").strip().upper()


def generate_voucher_code() -> str:
    return "".join(secrets.choice(VOUCHER_CODE_ALPHABET) for _ in range(VOUCHER_CODE_LENGTH))
