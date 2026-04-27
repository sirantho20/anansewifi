import os

from django.core.management.base import BaseCommand, CommandError

from network.models import NASDevice, Site


class Command(BaseCommand):
    help = (
        "Create or update a NASDevice row so Django can link RADIUS accounting "
        "NAS-IP-Address to a site. Use the hotspot gateway (LAN) if that is what MikroTik sends in "
        "NAS-IP-Address; use the WAN / RADIUS client IP if it matches accounting (same as RADIUS_NAS_CLIENT_IP)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "ip",
            nargs="?",
            help="Hotspot / NAS-IP-Address to match (e.g. 192.168.10.1). "
            "Default: RADIUS_NAS_DEVICE_IP from the environment.",
        )
        parser.add_argument(
            "--name",
            default="",
            help="NAS display name. Default: RADIUS_NAS_DEVICE_NAME or 'Production NAS'.",
        )
        parser.add_argument(
            "--site",
            default="",
            help="Site name to attach to. Default: RADIUS_NAS_DEVICE_SITE or first active Site. "
            "If no Site with this name exists, it is created.",
        )
        parser.add_argument(
            "--hotspot-subnet",
            default="",
            help="When creating a Site, set hotspot_subnet (CIDR), e.g. 192.168.20.0/24. "
            "Or set RADIUS_NAS_HOTSPOT_SUBNET in the environment.",
        )
        parser.add_argument(
            "--secret",
            default="",
            help="Stored NAS secret (metadata). Default: RADIUS_NAS_DEVICE_SECRET or RADIUS_CLIENT_SECRET env.",
        )

    def handle(self, *args, **options):
        ip = (options.get("ip") or os.environ.get("RADIUS_NAS_DEVICE_IP", "")).strip()
        if not ip:
            raise CommandError(
                "Provide an IP argument or set RADIUS_NAS_DEVICE_IP in the environment."
            )
        name = (options.get("name") or os.environ.get("RADIUS_NAS_DEVICE_NAME", "")).strip() or "Production NAS"
        site_name = (options.get("site") or os.environ.get("RADIUS_NAS_DEVICE_SITE", "")).strip()
        secret = (options.get("secret") or os.environ.get("RADIUS_NAS_DEVICE_SECRET", "")).strip() or os.environ.get(
            "RADIUS_CLIENT_SECRET", "ananse-radius-secret"
        )

        if site_name:
            hs = (options.get("hotspot_subnet") or os.environ.get("RADIUS_NAS_HOTSPOT_SUBNET", "")).strip()
            site, site_created = Site.objects.get_or_create(
                name=site_name,
                defaults={
                    "is_active": True,
                    "hotspot_subnet": hs,
                },
            )
            if site_created:
                self.stdout.write(self.style.WARNING(f'Created Site: {site_name}'))
        else:
            site = Site.objects.filter(is_active=True).order_by("name").first()
            if not site:
                site = Site.objects.create(
                    name="Main Site",
                    is_active=True,
                )
                self.stdout.write(self.style.WARNING("Created default Site: Main Site"))

        obj, created = NASDevice.objects.update_or_create(
            site=site,
            ip_address=ip,
            defaults={
                "name": name,
                "secret": secret,
                "shortname": name[:64],
                "is_active": True,
                "description": "RADIUS client source (WAN) IP; must match RADIUS_NAS_CLIENT_IP in FreeRADIUS clients.conf",
            },
        )
        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} NASDevice: {obj}"))
