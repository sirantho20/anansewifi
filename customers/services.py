import re
from dataclasses import dataclass

from .models import Customer

GHANA_COUNTRY_CODE = "233"


def normalize_mobile(raw_mobile: str) -> str:
    cleaned = re.sub(r"[^\d+]", "", raw_mobile.strip())
    if cleaned.startswith("+"):
        digits = cleaned[1:]
        if digits.startswith(GHANA_COUNTRY_CODE) and len(digits) == 12:
            return f"+{digits}"
        raise ValueError("Invalid mobile number format.")

    digits = re.sub(r"\D", "", cleaned)
    if digits.startswith("0") and len(digits) == 10:
        return f"+{GHANA_COUNTRY_CODE}{digits[1:]}"
    if digits.startswith(GHANA_COUNTRY_CODE) and len(digits) == 12:
        return f"+{digits}"
    if len(digits) == 9:
        return f"+{GHANA_COUNTRY_CODE}{digits}"
    raise ValueError("Invalid mobile number format.")


def generate_username_from_mobile(normalized_mobile: str) -> str:
    digits = re.sub(r"\D", "", normalized_mobile)
    return f"cust-{digits}"


@dataclass
class CustomerUpsertResult:
    customer: Customer
    created: bool


def get_or_create_customer(full_name: str, mobile: str) -> CustomerUpsertResult:
    normalized_mobile = normalize_mobile(mobile)
    customer = Customer.objects.filter(phone=normalized_mobile).first()
    if customer:
        update_fields = []
        if full_name and customer.full_name != full_name:
            customer.full_name = full_name
            update_fields.append("full_name")
        if update_fields:
            customer.save(update_fields=[*update_fields, "updated_at"])
        return CustomerUpsertResult(customer=customer, created=False)

    base_username = generate_username_from_mobile(normalized_mobile)
    username = base_username
    suffix = 1
    while Customer.objects.filter(username=username).exists():
        suffix += 1
        username = f"{base_username}-{suffix}"

    created_customer = Customer.objects.create(
        username=username,
        full_name=full_name.strip() or username,
        phone=normalized_mobile,
    )
    return CustomerUpsertResult(customer=created_customer, created=True)


def find_customer_by_identity(identity: str) -> Customer | None:
    if not identity:
        return None
    trimmed_identity = identity.strip()
    try:
        normalized_mobile = normalize_mobile(trimmed_identity)
    except ValueError:
        normalized_mobile = None

    if normalized_mobile:
        customer = Customer.objects.filter(phone=normalized_mobile).first()
        if customer:
            return customer
    return Customer.objects.filter(username=trimmed_identity).first()
