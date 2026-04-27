"""Idempotent creation of default retail unlimited plans (used at deploy and by management command)."""

from __future__ import annotations

from decimal import Decimal

from plans.models import BillingType, Plan, QuotaType, SpeedProfile

DEFAULT_SPEED_PROFILE = {
    "name": "Default Hotspot",
    "up_rate_kbps": 2048,
    "down_rate_kbps": 4096,
    "mikrotik_rate_limit": "2M/4M",
}

DEFAULT_UNLIMITED_PLAN_SPECS: list[dict[str, object]] = [
    {
        "name": "1 Day Unlimited",
        "description": "Unlimited data for 24 hours on one device.",
        "price": Decimal("3.00"),
        "duration_minutes": 1440,
        "session_timeout_seconds": 86400,
        "idle_timeout_seconds": 1800,
    },
    {
        "name": "1 Week Unlimited",
        "description": "Unlimited data for 7 days on one device.",
        "price": Decimal("15.00"),
        "duration_minutes": 10080,
        "session_timeout_seconds": 604800,
        "idle_timeout_seconds": 3600,
    },
    {
        "name": "1 Month Unlimited",
        "description": "Unlimited data for 30 days on one device.",
        "price": Decimal("50.00"),
        "duration_minutes": 43200,
        "session_timeout_seconds": 2592000,
        "idle_timeout_seconds": 3600,
    },
]


def ensure_default_unlimited_plans() -> int:
    """
    Ensure the default speed profile and three unlimited voucher plans exist (get_or_create by name).

    Does not overwrite existing plans, so admin changes to price or limits are preserved.

    Returns the number of plans newly created (0–3).
    """
    speed, _ = SpeedProfile.objects.get_or_create(
        name=DEFAULT_SPEED_PROFILE["name"],
        defaults={
            "up_rate_kbps": DEFAULT_SPEED_PROFILE["up_rate_kbps"],
            "down_rate_kbps": DEFAULT_SPEED_PROFILE["down_rate_kbps"],
            "mikrotik_rate_limit": DEFAULT_SPEED_PROFILE["mikrotik_rate_limit"],
        },
    )

    created_count = 0
    for row in DEFAULT_UNLIMITED_PLAN_SPECS:
        name = str(row["name"])
        _, was_created = Plan.objects.get_or_create(
            name=name,
            defaults={
                "description": str(row["description"]),
                "price": row["price"],
                "billing_type": BillingType.VOUCHER,
                "quota_type": QuotaType.UNLIMITED,
                "duration_minutes": int(row["duration_minutes"]),
                "data_bytes": None,
                "speed_profile": speed,
                "concurrent_device_limit": 1,
                "idle_timeout_seconds": int(row["idle_timeout_seconds"]),
                "session_timeout_seconds": int(row["session_timeout_seconds"]),
                "is_active": True,
                "is_featured": False,
            },
        )
        if was_created:
            created_count += 1
    return created_count
