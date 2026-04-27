from django.core.management.base import BaseCommand

from plans.default_plans import ensure_default_unlimited_plans


class Command(BaseCommand):
    help = (
        "Ensure default unlimited voucher plans exist (idempotent). "
        "Run after migrate so DATABASE_URL / PostgreSQL always has the base retail plans."
    )

    def handle(self, *args, **options):
        n = ensure_default_unlimited_plans()
        if n:
            self.stdout.write(self.style.SUCCESS(f"Created {n} default plan(s)."))
        else:
            self.stdout.write("Default plans already present (nothing new created).")
