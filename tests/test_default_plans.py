"""Default unlimited plans (migration + ensure_default_plans command)."""

import pytest
from django.core.management import call_command

from plans.default_plans import DEFAULT_UNLIMITED_PLAN_SPECS
from plans.models import BillingType, Plan, QuotaType


DEFAULT_UNLIMITED_NAMES = tuple(str(s["name"]) for s in DEFAULT_UNLIMITED_PLAN_SPECS)


@pytest.mark.django_db
def test_default_unlimited_plans_seeded_by_migration():
    assert Plan.objects.filter(name__in=DEFAULT_UNLIMITED_NAMES).count() == 3
    for name in DEFAULT_UNLIMITED_NAMES:
        plan = Plan.objects.get(name=name)
        assert plan.quota_type == QuotaType.UNLIMITED
        assert plan.concurrent_device_limit == 1
        assert plan.data_bytes is None
        assert plan.billing_type == BillingType.VOUCHER
        assert plan.is_active is True
        assert plan.speed_profile is not None
        assert plan.speed_profile.name == "Default Hotspot"

    day, week, month = (Plan.objects.get(name=n) for n in DEFAULT_UNLIMITED_NAMES)
    assert day.duration_minutes == 1440
    assert day.price == 3
    assert day.session_timeout_seconds == 86400

    assert week.duration_minutes == 10080
    assert week.price == 15
    assert week.session_timeout_seconds == 604800

    assert month.duration_minutes == 43200
    assert month.price == 50
    assert month.session_timeout_seconds == 2592000


@pytest.mark.django_db
def test_ensure_default_plans_command_repairs_missing_rows():
    Plan.objects.filter(name__in=DEFAULT_UNLIMITED_NAMES).delete()
    assert Plan.objects.filter(name__in=DEFAULT_UNLIMITED_NAMES).count() == 0

    call_command("ensure_default_plans")
    assert Plan.objects.filter(name__in=DEFAULT_UNLIMITED_NAMES).count() == 3

    call_command("ensure_default_plans")
    assert Plan.objects.filter(name__in=DEFAULT_UNLIMITED_NAMES).count() == 3
