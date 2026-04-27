from django.test import TestCase

from customers.models import Customer
from plans.models import Plan, SpeedProfile
from vouchers.models import Voucher, VoucherStatus

from .models import Session
from .services import ingest_accounting_event


class IngestAccountingEventTests(TestCase):
    def test_resolves_customer_when_username_matches_voucher_code(self):
        speed_profile = SpeedProfile.objects.create(
            name="AcctVouch",
            up_rate_kbps=1024,
            down_rate_kbps=2048,
            mikrotik_rate_limit="1M/2M",
        )
        plan = Plan.objects.create(
            name="Acct Plan",
            price=5,
            duration_minutes=60,
            speed_profile=speed_profile,
            idle_timeout_seconds=300,
            session_timeout_seconds=1800,
        )
        customer = Customer.objects.create(username="acct-msisdn", full_name="Acct User")
        voucher = Voucher.objects.create(
            code="ANW-ACCT-VC-01",
            plan=plan,
            status=VoucherStatus.REDEEMED,
            redeemed_by=customer,
        )
        ingest_accounting_event(
            {
                "event_type": "start",
                "username": voucher.code,
                "session_id": "sess-voucher-as-name",
                "framed_ip_address": "10.1.1.9",
                "calling_station_id": "AA-BB-CC-DD-EE-99",
                "nas_ip_address": "192.168.10.1",
                "input_octets": 0,
                "output_octets": 0,
                "duration_seconds": 0,
            }
        )
        session = Session.objects.get(session_id="sess-voucher-as-name")
        self.assertEqual(session.customer_id, customer.id)
        self.assertEqual(session.username, voucher.code)
