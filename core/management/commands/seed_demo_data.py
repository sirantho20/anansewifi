from decimal import Decimal

from django.core.management.base import BaseCommand

from customers.models import Customer
from network.models import NASDevice, Site
from plans.models import BillingType, Plan, QuotaType, SpeedProfile
from vouchers.models import Voucher, VoucherBatch


class Command(BaseCommand):
    help = "Seed demo data for local lab testing. Base retail plans (1 day / week / month unlimited) are created by the plans.0004_default_unlimited_plans migration."

    def handle(self, *args, **options):
        speed_profile, _ = SpeedProfile.objects.get_or_create(
            name="Starter Speed",
            defaults={
                "up_rate_kbps": 2048,
                "down_rate_kbps": 4096,
                "mikrotik_rate_limit": "2M/4M",
            },
        )
        plan = Plan.objects.filter(
            name="Hourly 1GB",
            price=5.00,
            duration_minutes=60,
        ).first()
        if not plan:
            plan = Plan.objects.create(
                name="Hourly 1GB",
                description="1 hour access with 1GB quota",
                price=5.00,
                duration_minutes=60,
                data_bytes=1024 * 1024 * 1024,
                speed_profile=speed_profile,
            )

        extra_plans = [
            {
                "name": "Daily Pass",
                "description": (
                    "Full-day Wi‑Fi for visitors and remote workers who need a single, "
                    "simple window from first login through midnight. No hourly top-ups—"
                    "just connect, work, stream, and sign off when the day ends."
                ),
                "price": Decimal("25.00"),
                "quota_type": QuotaType.DURATION,
                "duration_minutes": 24 * 60,
                "data_bytes": None,
            },
            {
                "name": "Weekend Special",
                "description": (
                    "Friday evening through Sunday night coverage for pop-up shops, "
                    "house guests, and small events. Designed so your hotspot can stay "
                    "busy all weekend without you babysitting voucher codes."
                ),
                "price": Decimal("35.00"),
                "quota_type": QuotaType.DURATION,
                "duration_minutes": 48 * 60,
                "data_bytes": None,
            },
            {
                "name": "Quick Drop-In (45 min)",
                "description": (
                    "Short, affordable session for people who only need to grab email, "
                    "send a file, or message home before they head out. Perfect near "
                    "transport hubs, cafés, and reception desks."
                ),
                "price": Decimal("2.50"),
                "quota_type": QuotaType.DURATION,
                "duration_minutes": 45,
                "data_bytes": None,
            },
            {
                "name": "Heavy Data Boost (5 GB)",
                "description": (
                    "Data-first pack for uploads, cloud sync, and HD calls when clock "
                    "time matters less than megabytes. Stops automatically when the "
                    "allowance is used—great for creators on a tight budget."
                ),
                "price": Decimal("18.00"),
                "quota_type": QuotaType.DATA,
                "duration_minutes": None,
                "data_bytes": 5 * 1024 * 1024 * 1024,
            },
        ]
        for row in extra_plans:
            Plan.objects.get_or_create(
                name=row["name"],
                defaults={
                    "description": row["description"],
                    "price": row["price"],
                    "billing_type": BillingType.VOUCHER,
                    "quota_type": row["quota_type"],
                    "duration_minutes": row["duration_minutes"],
                    "data_bytes": row["data_bytes"],
                    "speed_profile": speed_profile,
                    "is_active": True,
                },
            )

        customer, _ = Customer.objects.get_or_create(
            username="demo-customer",
            defaults={
                "full_name": "Demo Customer",
                "phone": "+233200000000",
                "email": "demo@example.com",
            },
        )
        site = Site.objects.filter(name="Lab Main Site").first()
        if not site:
            site = Site.objects.create(
                name="Lab Main Site",
                hotspot_subnet="172.20.20.0/24",
                management_subnet="172.20.30.0/24",
            )
        NASDevice.objects.get_or_create(
            site=site,
            ip_address="172.20.20.1",
            defaults={
                "name": "CHR-Lab",
                "secret": "ananse-radius-secret",
                "shortname": "chr-lab",
            },
        )
        batch, _ = VoucherBatch.objects.get_or_create(
            name="Demo Batch",
            plan=plan,
            defaults={"code_prefix": "DEMO", "quantity": 3},
        )
        for code in ("DEMO01", "DEMO02", "DEMO03"):
            Voucher.objects.get_or_create(
                code=code,
                defaults={
                    "plan": plan,
                    "batch": batch,
                    "status": "available",
                },
            )

        Plan.objects.update(is_featured=False)
        featured = Plan.objects.filter(name="Daily Pass", is_active=True).first()
        if featured:
            featured.is_featured = True
            featured.save(update_fields=["is_featured", "updated_at"])

        self.stdout.write(self.style.SUCCESS(f"Demo data ready for {customer.username}"))
