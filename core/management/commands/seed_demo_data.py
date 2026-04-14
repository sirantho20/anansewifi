from django.core.management.base import BaseCommand

from customers.models import Customer
from network.models import NASDevice, Site
from plans.models import Plan, SpeedProfile
from vouchers.models import Voucher, VoucherBatch


class Command(BaseCommand):
    help = "Seed demo data for local lab testing."

    def handle(self, *args, **options):
        speed_profile, _ = SpeedProfile.objects.get_or_create(
            code="starter-speed",
            defaults={
                "name": "Starter Speed",
                "up_rate_kbps": 2048,
                "down_rate_kbps": 4096,
                "mikrotik_rate_limit": "2M/4M",
            },
        )
        plan, _ = Plan.objects.get_or_create(
            code="hourly-1gb",
            defaults={
                "name": "Hourly 1GB",
                "description": "1 hour access with 1GB quota",
                "price": 5.00,
                "duration_minutes": 60,
                "data_bytes": 1024 * 1024 * 1024,
                "speed_profile": speed_profile,
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
        site, _ = Site.objects.get_or_create(
            code="lab-main",
            defaults={
                "name": "Lab Main Site",
                "hotspot_subnet": "172.20.20.0/24",
                "management_subnet": "172.20.30.0/24",
            },
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
            defaults={"code_prefix": "ANW", "quantity": 3},
        )
        for code in ("ANW-DEMO-001", "ANW-DEMO-002", "ANW-DEMO-003"):
            Voucher.objects.get_or_create(
                code=code,
                defaults={
                    "plan": plan,
                    "batch": batch,
                    "status": "available",
                },
            )

        self.stdout.write(self.style.SUCCESS(f"Demo data ready for {customer.username}"))
