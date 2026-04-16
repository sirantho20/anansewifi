import base64
import json
import logging
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from http import HTTPStatus
from urllib import error, parse, request

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from customers.models import Customer
from customers.services import get_or_create_customer, normalize_mobile
from plans.models import Plan
from vouchers.models import Voucher

from .models import Payment, PaymentStatus

logger = logging.getLogger(__name__)


class PaymentProviderError(Exception):
    def __init__(
        self,
        message: str,
        *,
        provider: str = "paystack",
        http_status: int | None = None,
        code: str | None = None,
        error_type: str | None = None,
        meta: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.http_status = http_status
        self.code = str(code) if code is not None else None
        self.error_type = str(error_type) if error_type is not None else None
        self.meta = meta if isinstance(meta, dict) else None

    def to_metadata(self) -> dict:
        return {
            "provider": self.provider,
            "message": str(self),
            "http_status": self.http_status,
            "code": self.code,
            "type": self.error_type,
            "meta": self.meta or {},
        }


@dataclass
class PurchaseInitialization:
    customer: Customer
    payment: Payment
    authorization_url: str
    access_code: str
    reference: str


@dataclass
class PurchaseVerification:
    payment: Payment
    voucher: Voucher | None
    sms_sent: bool
    sms_error: str
    customer: Customer


class PaystackClient:
    def __init__(self) -> None:
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.base_url = settings.PAYSTACK_BASE_URL.rstrip("/")

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        if not self.secret_key:
            raise PaymentProviderError("Paystack secret key is missing.")

        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}{path}"
        timeout = 20
        try:
            if method.upper() == "POST":
                response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            elif method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            else:
                raise PaymentProviderError(f"Unsupported Paystack HTTP method: {method}")
        except requests.RequestException as exc:
            raise PaymentProviderError(f"Paystack connection failed: {exc}") from exc

        parsed: dict | None = None
        if response.content:
            try:
                body = response.json()
            except ValueError:
                body = None
            parsed = body if isinstance(body, dict) else None

        if not response.ok:
            fallback = (
                (response.text or "").strip()
                or (str(parsed.get("message")) if isinstance(parsed, dict) and parsed.get("message") else "")
                or f"Paystack HTTP error ({response.status_code})."
            )
            raise self._build_error(
                fallback_message=fallback,
                parsed_payload=parsed,
                http_status=response.status_code,
            )

        if not isinstance(parsed, dict):
            raise PaymentProviderError("Unexpected Paystack response format.")
        if not parsed.get("status"):
            raise self._build_error(
                fallback_message="Paystack request failed.",
                parsed_payload=parsed,
                http_status=response.status_code,
            )
        return parsed["data"]

    @staticmethod
    def _build_error(
        *,
        fallback_message: str,
        parsed_payload: dict | None,
        http_status: int | None,
    ) -> PaymentProviderError:
        if parsed_payload:
            message = str(parsed_payload.get("message") or fallback_message)
            code = parsed_payload.get("code")
            error_type = parsed_payload.get("type")
            meta = parsed_payload.get("meta") if isinstance(parsed_payload.get("meta"), dict) else None
            return PaymentProviderError(
                message,
                http_status=http_status,
                code=code,
                error_type=error_type,
                meta=meta,
            )
        return PaymentProviderError(fallback_message, http_status=http_status)

    def initialize_transaction(
        self,
        *,
        email: str,
        amount_pesewas: int,
        callback_url: str,
        metadata: dict,
        reference: str | None = None,
    ) -> dict:
        payload: dict = {
            "email": email,
            "amount": amount_pesewas,
            "callback_url": callback_url,
            "currency": settings.PAYMENT_CURRENCY,
            "metadata": metadata,
        }
        if reference:
            payload["reference"] = reference
        return self._request("POST", "/transaction/initialize", payload=payload)

    def verify_transaction(self, reference: str) -> dict:
        escaped_ref = parse.quote(reference, safe="")
        return self._request("GET", f"/transaction/verify/{escaped_ref}")


class HubtelClient:
    def __init__(self) -> None:
        self.client_id = settings.HUBTEL_CLIENT_ID
        self.client_secret = settings.HUBTEL_CLIENT_SECRET
        self.sender_id = settings.HUBTEL_SENDER_ID
        self.base_url = settings.HUBTEL_BASE_URL.rstrip("/")
        self.send_path = settings.HUBTEL_SMS_SEND_PATH
        self.timeout_seconds = settings.HUBTEL_TIMEOUT_SECONDS

    @staticmethod
    def _is_success_status(status: object) -> bool:
        normalized = str(status).strip().lower()
        return normalized in {"0", "200", "success", "ok", "accepted", "true"}

    @staticmethod
    def _extract_error_message(payload: dict | None, fallback: str) -> str:
        if not payload:
            return fallback
        for key in ("Message", "message", "Error", "error", "Description", "description"):
            value = payload.get(key)
            if value:
                return str(value)
        errors = payload.get("Errors") or payload.get("errors")
        if isinstance(errors, list) and errors:
            first_error = errors[0]
            if isinstance(first_error, dict):
                for key in ("message", "Message", "description", "Description"):
                    value = first_error.get(key)
                    if value:
                        return str(value)
            return str(first_error)
        return fallback

    def send_sms(self, *, to_number: str, message: str) -> tuple[bool, str]:
        if not self.client_id or not self.client_secret:
            return False, "Hubtel credentials are missing."

        from_value = str(self.sender_id or "").strip()
        to_value = str(to_number or "").strip()
        content_value = str(message or "").strip()
        if not from_value:
            return False, "Hubtel sender ID is missing."
        if not to_value:
            return False, "Recipient number is missing."
        if not content_value:
            return False, "SMS content is empty."

        credentials = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        auth_header = base64.b64encode(credentials).decode("utf-8")
        payload = {
            "From": from_value,
            "To": to_value,
            "Content": content_value,
            "RegisteredDelivery": True,
        }
        req = request.Request(
            url=f"{self.base_url}{self.send_path}",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/json",
            },
        )
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw_response = response.read().decode("utf-8").strip()
                body = json.loads(raw_response) if raw_response else {}
                status = body.get("Status") or body.get("status") or response.status
                if self._is_success_status(status):
                    return True, ""
                fallback = "Hubtel send failed."
                return False, self._extract_error_message(body, fallback)
        except error.HTTPError as exc:
            raw_detail = exc.read().decode("utf-8").strip()
            parsed = None
            if raw_detail:
                try:
                    parsed = json.loads(raw_detail)
                except json.JSONDecodeError:
                    parsed = None
            fallback = f"{HTTPStatus(exc.code).phrase} ({exc.code})" if exc.code else "Hubtel HTTP error"
            message_text = self._extract_error_message(parsed, raw_detail or fallback)
            return False, f"Hubtel HTTP error: {message_text}"
        except error.URLError as exc:
            return False, f"Hubtel connection error: {exc.reason}"


def _decimal_to_pesewas(amount: Decimal) -> int:
    return int((amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _generate_voucher_code() -> str:
    token = timezone.now().strftime("%y%m%d%H%M%S%f")[-10:]
    return f"ANW-PUR-{token}"


def _build_customer_email(customer: Customer) -> str:
    if customer.email:
        return customer.email
    # Paystack rejects some synthetic TLDs (e.g. .local); use a reserved-domain placeholder.
    return f"paystack+customer-{customer.pk}@example.com"


def initialize_plan_purchase(
    *,
    plan: Plan,
    full_name: str,
    mobile: str,
    callback_url: str | None = None,
) -> PurchaseInitialization:
    upsert_result = get_or_create_customer(full_name=full_name, mobile=mobile)
    customer = upsert_result.customer

    payment = Payment.objects.create(
        customer=customer,
        plan=plan,
        amount=plan.price,
        provider="paystack",
        status=PaymentStatus.PENDING,
        provider_reference="",
        metadata={
            "full_name": customer.full_name,
            "mobile": customer.phone,
            "customer_created": upsert_result.created,
            "currency": settings.PAYMENT_CURRENCY,
        },
    )

    effective_callback = (callback_url or "").strip() or settings.PAYSTACK_CALLBACK_URL

    paystack_client = PaystackClient()
    try:
        paystack_data = paystack_client.initialize_transaction(
            email=_build_customer_email(customer),
            amount_pesewas=_decimal_to_pesewas(plan.price),
            callback_url=effective_callback,
            metadata={
                "payment_id": str(payment.id),
                "customer_id": str(customer.id),
                "plan_id": str(plan.id),
            },
        )
    except Exception as exc:
        payment.status = PaymentStatus.FAILED
        metadata = payment.metadata or {}
        metadata["initialize_error"] = str(exc)
        if isinstance(exc, PaymentProviderError):
            metadata["paystack_initialize_error"] = exc.to_metadata()
        else:
            metadata["paystack_initialize_error"] = {
                "provider": "paystack",
                "message": str(exc),
            }
        payment.metadata = metadata
        payment.save(update_fields=["status", "metadata", "updated_at"])
        logger.warning(
            "Paystack initialize failed payment_id=%s reference=%s error=%s",
            payment.id,
            payment.provider_reference or "(unset)",
            str(exc),
        )
        raise

    paystack_reference = str(paystack_data.get("reference") or "").strip()
    if not paystack_reference:
        payment.status = PaymentStatus.FAILED
        metadata = payment.metadata or {}
        metadata["initialize_error"] = "Paystack initialize response missing reference."
        payment.metadata = metadata
        payment.save(update_fields=["status", "metadata", "updated_at"])
        raise PaymentProviderError("Paystack initialize response missing reference.")

    metadata = payment.metadata or {}
    metadata["paystack_initialize"] = {
        "access_code": paystack_data.get("access_code", ""),
        "authorization_url": paystack_data.get("authorization_url", ""),
        "reference": paystack_reference,
    }
    payment.metadata = metadata
    payment.provider_reference = paystack_reference
    payment.save(update_fields=["metadata", "provider_reference", "updated_at"])

    return PurchaseInitialization(
        customer=customer,
        payment=payment,
        authorization_url=paystack_data["authorization_url"],
        access_code=paystack_data.get("access_code", ""),
        reference=paystack_reference,
    )


def _validate_transaction(payment: Payment, paystack_payload: dict) -> None:
    status = str(paystack_payload.get("status", "")).lower()
    if status != "success":
        raise PaymentProviderError("Payment was not successful.")

    expected_amount = _decimal_to_pesewas(payment.amount)
    received_amount = int(paystack_payload.get("amount") or 0)
    if expected_amount != received_amount:
        raise PaymentProviderError("Paid amount does not match selected plan.")

    expected_currency = settings.PAYMENT_CURRENCY.upper()
    received_currency = str(paystack_payload.get("currency", "")).upper()
    if received_currency and received_currency != expected_currency:
        raise PaymentProviderError("Paid currency does not match system currency.")


def _create_voucher_for_payment(payment: Payment) -> Voucher:
    attempts = 0
    while attempts < 5:
        code = _generate_voucher_code()
        if not Voucher.objects.filter(code=code).exists():
            return Voucher.objects.create(
                code=code,
                plan=payment.plan,
                max_uses=1,
                use_count=0,
            )
        attempts += 1
    raise PaymentProviderError("Unable to generate a unique voucher code.")


def _send_voucher_sms(customer: Customer, voucher: Voucher) -> tuple[bool, str]:
    if not customer.phone:
        return False, "Customer mobile number is missing."
    sms_message = (
        f"Hi {customer.full_name}, your Ananse WiFi voucher is {voucher.code}. "
        "Go to the portal login page, enter this code, and connect."
    )
    hubtel_client = HubtelClient()
    return hubtel_client.send_sms(to_number=customer.phone, message=sms_message)


def verify_plan_purchase(reference: str) -> PurchaseVerification:
    payment = (
        Payment.objects.select_related("customer", "plan", "voucher")
        .filter(provider="paystack", provider_reference=reference)
        .first()
    )
    if not payment:
        raise PaymentProviderError("Payment reference was not found.")
    if not payment.plan:
        raise PaymentProviderError("Payment plan is missing.")

    paystack_client = PaystackClient()
    try:
        paystack_payload = paystack_client.verify_transaction(reference)
    except PaymentProviderError as exc:
        metadata = payment.metadata or {}
        metadata["verify_error"] = str(exc)
        metadata["paystack_verify_error"] = exc.to_metadata()
        payment.status = PaymentStatus.FAILED
        payment.metadata = metadata
        payment.save(update_fields=["status", "metadata", "updated_at"])
        logger.warning(
            "Paystack verify failed payment_id=%s reference=%s error=%s",
            payment.id,
            payment.provider_reference,
            str(exc),
        )
        raise
    try:
        _validate_transaction(payment, paystack_payload)
    except PaymentProviderError as exc:
        payment.status = PaymentStatus.FAILED
        metadata = payment.metadata or {}
        metadata["verify_error"] = str(exc)
        metadata["paystack_verify"] = paystack_payload
        payment.metadata = metadata
        payment.save(update_fields=["status", "metadata", "updated_at"])
        raise

    with transaction.atomic():
        locked_payment = Payment.objects.select_for_update().get(id=payment.id)
        if locked_payment.status == PaymentStatus.SUCCESS and locked_payment.voucher:
            sms_sent = bool((locked_payment.metadata or {}).get("sms_sent"))
            sms_error = str((locked_payment.metadata or {}).get("sms_error", ""))
            return PurchaseVerification(
                payment=locked_payment,
                voucher=locked_payment.voucher,
                sms_sent=sms_sent,
                sms_error=sms_error,
                customer=locked_payment.customer,
            )

        voucher = locked_payment.voucher or _create_voucher_for_payment(locked_payment)
        metadata = locked_payment.metadata or {}
        metadata["paystack_verify"] = {
            "paid_at": paystack_payload.get("paid_at"),
            "channel": paystack_payload.get("channel"),
            "authorization": paystack_payload.get("authorization", {}),
            "customer": paystack_payload.get("customer", {}),
        }
        locked_payment.metadata = metadata
        locked_payment.voucher = voucher
        locked_payment.status = PaymentStatus.SUCCESS
        locked_payment.save(update_fields=["metadata", "voucher", "status", "updated_at"])

    sms_sent, sms_error = _send_voucher_sms(locked_payment.customer, voucher)
    metadata = locked_payment.metadata or {}
    metadata["sms_sent"] = sms_sent
    metadata["sms_error"] = sms_error
    locked_payment.metadata = metadata
    locked_payment.save(update_fields=["metadata", "updated_at"])
    return PurchaseVerification(
        payment=locked_payment,
        voucher=voucher,
        sms_sent=sms_sent,
        sms_error=sms_error,
        customer=locked_payment.customer,
    )


def lookup_customer_by_mobile(mobile: str) -> Customer | None:
    try:
        normalized_mobile = normalize_mobile(mobile)
    except ValueError:
        return None
    return Customer.objects.filter(phone=normalized_mobile).first()
