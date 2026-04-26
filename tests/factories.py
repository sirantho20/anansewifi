import factory

from customers.models import Customer
from plans.models import Plan, SpeedProfile
from vouchers.models import Voucher


class SpeedProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SpeedProfile

    name = factory.Sequence(lambda n: f"Speed {n}")
    up_rate_kbps = 2048
    down_rate_kbps = 4096
    mikrotik_rate_limit = "2M/4M"


class PlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Plan

    name = factory.Sequence(lambda n: f"Plan {n}")
    price = 10
    duration_minutes = 60
    data_bytes = 1024 * 1024 * 1024
    is_featured = False
    speed_profile = factory.SubFactory(SpeedProfileFactory)


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    username = factory.Sequence(lambda n: f"customer{n}")
    full_name = "Sample Customer"
    phone = factory.Sequence(lambda n: f"+233200000{n:03d}")


class VoucherFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Voucher

    code = factory.Sequence(lambda n: f"ANW-{n:05d}")
    plan = factory.SubFactory(PlanFactory)
