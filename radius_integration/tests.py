from django.test import TestCase
from django.utils import timezone

from customers.models import Customer
from plans.models import Plan, SpeedProfile
from sessions.models import Entitlement, Session
from vouchers.models import Voucher, VoucherStatus

from .models import RadAcct, RadCheck, RadReply
from .services import (
    sync_entitlement_to_radius,
    sync_radacct_records,
    verify_radius_cleartext_password,
)


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

    def test_sync_entitlement_projects_voucher_code_as_second_username(self):
        speed_profile = SpeedProfile.objects.create(
            name="VoucherDup",
            up_rate_kbps=1024,
            down_rate_kbps=2048,
            mikrotik_rate_limit="1M/2M",
        )
        plan = Plan.objects.create(
            name="Voucher Dup Plan",
            price=5,
            duration_minutes=60,
            speed_profile=speed_profile,
            idle_timeout_seconds=300,
            session_timeout_seconds=1800,
        )
        customer = Customer.objects.create(username="dup-user", full_name="Dup User")
        voucher = Voucher.objects.create(
            code="ANW-DUP-RAD-001",
            plan=plan,
            status=VoucherStatus.REDEEMED,
            redeemed_by=customer,
        )
        entitlement = Entitlement.objects.create(
            customer=customer,
            plan=plan,
            voucher=voucher,
            status="active",
        )
        sync_entitlement_to_radius(
            username=customer.username,
            cleartext_password=voucher.code,
            entitlement=entitlement,
        )
        self.assertTrue(
            RadCheck.objects.filter(
                username="dup-user",
                attribute="Cleartext-Password",
                value=voucher.code,
            ).exists()
        )
        self.assertTrue(
            RadCheck.objects.filter(
                username=voucher.code,
                attribute="Cleartext-Password",
                value=voucher.code,
            ).exists()
        )
        self.assertTrue(
            RadReply.objects.filter(
                username=voucher.code,
                attribute="Mikrotik-Rate-Limit",
                value="1M/2M",
            ).exists()
        )


class VerifyRadiusCleartextPasswordTests(TestCase):
    def test_accepts_matching_password(self):
        speed_profile = SpeedProfile.objects.create(
            name="VerifySpeed",
            up_rate_kbps=1024,
            down_rate_kbps=2048,
            mikrotik_rate_limit="1M/2M",
        )
        plan = Plan.objects.create(
            name="Verify Plan",
            price=5,
            duration_minutes=60,
            speed_profile=speed_profile,
            idle_timeout_seconds=300,
            session_timeout_seconds=1800,
        )
        customer = Customer.objects.create(username="verify-user", full_name="Verify User")
        entitlement = Entitlement.objects.create(customer=customer, plan=plan, status="active")
        sync_entitlement_to_radius(
            username=customer.username,
            cleartext_password="secret-code",
            entitlement=entitlement,
        )
        self.assertTrue(
            verify_radius_cleartext_password(customer=customer, cleartext_password="secret-code"),
        )
        self.assertFalse(
            verify_radius_cleartext_password(customer=customer, cleartext_password="wrong"),
        )
        self.assertFalse(verify_radius_cleartext_password(customer=customer, cleartext_password=""))
        no_row = Customer.objects.create(username="no-radcheck", full_name="No Row")
        self.assertFalse(
            verify_radius_cleartext_password(customer=no_row, cleartext_password="anything"),
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
