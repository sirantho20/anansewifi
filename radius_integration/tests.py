from django.test import TestCase
from django.utils import timezone

from customers.models import Customer
from plans.models import Plan, SpeedProfile
from sessions.models import Entitlement, Session

from .models import RadAcct, RadCheck, RadReply
from .services import sync_entitlement_to_radius, sync_radacct_records


class RadiusProjectionTests(TestCase):
    def test_sync_entitlement_projects_to_radcheck_and_radreply(self):
        speed_profile = SpeedProfile.objects.create(
            name="Starter",
            up_rate_kbps=1024,
            down_rate_kbps=2048,
            mikrotik_rate_limit="1M/2M",
        )
        plan = Plan.objects.create(
            name="Starter Plan",
            price=5,
            duration_minutes=60,
            speed_profile=speed_profile,
            idle_timeout_seconds=300,
            session_timeout_seconds=1800,
        )
        customer = Customer.objects.create(username="project-user", full_name="Project User")
        entitlement = Entitlement.objects.create(customer=customer, plan=plan, status="active")

        sync_entitlement_to_radius(
            username=customer.username,
            cleartext_password="voucher-123",
            entitlement=entitlement,
        )

        self.assertTrue(
            RadCheck.objects.filter(
                username="project-user",
                attribute="Cleartext-Password",
                value="voucher-123",
            ).exists()
        )
        self.assertTrue(
            RadReply.objects.filter(
                username="project-user",
                attribute="Mikrotik-Rate-Limit",
                value="1M/2M",
            ).exists()
        )


class RadAcctConsumptionTests(TestCase):
    def test_sync_radacct_records_updates_sessions(self):
        start_at = timezone.now()
        RadAcct.objects.create(
            acctsessionid="radacct-session-1",
            acctuniqueid="unique-session-1",
            username="acct-user",
            acctstarttime=start_at,
            acctsessiontime=120,
            acctinputoctets=1200,
            acctoutputoctets=3400,
            callingstationid="AA-BB-CC-DD-EE-FF",
            nasipaddress="172.20.20.1",
            framedipaddress="10.0.0.10",
        )

        processed = sync_radacct_records()
        self.assertEqual(processed, 1)

        session = Session.objects.get(session_id="radacct-session-1")
        self.assertEqual(session.username, "acct-user")
        self.assertEqual(session.total_octets, 4600)
        self.assertEqual(session.duration_seconds, 120)

        # Re-running should be idempotent due to sync checkpoint.
        self.assertEqual(sync_radacct_records(), 0)
