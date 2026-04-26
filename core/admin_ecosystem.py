"""Admin helpers: ecosystem copy for change forms."""

from __future__ import annotations

from typing import Any

from django.utils.safestring import SafeString, mark_safe


def _html(*paragraphs: str) -> SafeString:
    body = "".join(
        f'<p class="mb-2 last:mb-0">{p}</p>'
        for p in paragraphs
    )
    return mark_safe(body)


ECOSYSTEM_SUMMARIES: dict[str, SafeString] = {
    "accounts.staffprofile": _html(
        "<strong>Role</strong>: Links a Django auth user to operator metadata (role, phone, active). "
        "This is admin/portal access control, not end-user hotspot identity.",
        "<strong>Important fields</strong>: <code>user</code> (who logs in), <code>role</code> (permissions "
        "grouping in your app), <code>is_active</code> (revoke access without deleting the user).",
        "<strong>Chain</strong>: Staff authenticate against <code>auth.User</code>; this profile is "
        "consulted for operator UI and auditing, not for RADIUS.",
    ),
    "customers.customer": _html(
        "<strong>Role</strong>: Canonical hotspot subscriber identity—who bought access, redeems vouchers, "
        "and owns devices.",
        "<strong>Important fields</strong>: <code>username</code> (unique login id), <code>phone</code> "
        "(optional unique id for payments), <code>is_active</code>, <code>last_seen_at</code> (ops/CRM).",
        "<strong>Chain</strong>: Feeds <code>Payment</code>, <code>Device</code>, <code>Entitlement</code>, "
        "and <code>Session</code>; portal flows resolve the customer before granting access.",
    ),
    "customers.device": _html(
        "<strong>Role</strong>: MAC address bound to a customer for multi-device / trust policies.",
        "<strong>Important fields</strong>: <code>customer</code>, <code>mac_address</code> (unique per "
        "customer), <code>is_trusted</code> (policy), <code>last_seen_at</code>.",
        "<strong>Chain</strong>: Used alongside RADIUS calling-station-id / portal MAC checks; ties "
        "hardware to <code>Customer</code> for session limits and support.",
    ),
    "plans.speedprofile": _html(
        "<strong>Role</strong>: Rate-limit template (up/down kbps, MikroTik-style string) shared by plans.",
        "<strong>Important fields</strong>: <code>name</code> (unique reference), "
        "<code>mikrotik_rate_limit</code> (what NAS/RADIUS reply attributes often mirror), rates in kbps.",
        "<strong>Chain</strong>: <code>Plan</code> references a profile; entitlements inherit it; "
        "RADIUS replies / CoA may emit matching attributes for the NAS.",
    ),
    "plans.plan": _html(
        "<strong>Role</strong>: Sellable package: price, quota (time/data), speed, session limits, "
        "billing mode (voucher vs direct vs manual).",
        "<strong>Important fields</strong>: <code>quota_type</code>, <code>duration_minutes</code>, "
        "<code>data_bytes</code>, <code>speed_profile</code>, <code>concurrent_device_limit</code>, "
        "timeouts, <code>is_active</code>.",
        "<strong>Chain</strong>: Drives <code>Voucher</code>/<code>VoucherBatch</code>, "
        "<code>Payment</code>, and <code>Entitlement</code>; defines what access the user is buying.",
    ),
    "vouchers.voucherbatch": _html(
        "<strong>Role</strong>: Operator-defined run of vouchers: which plan, how many, optional batch expiry.",
        "<strong>Important fields</strong>: <code>plan</code>, <code>quantity</code>, "
        "<code>code_prefix</code>, <code>expires_at</code>.",
        "<strong>Chain</strong>: Generates or groups <code>Voucher</code> rows; redemption still keys "
        "off each voucher’s plan and state.",
    ),
    "vouchers.voucher": _html(
        "<strong>Role</strong>: Redeemable access code tied to a plan; bridges prepaid retail to entitlements.",
        "<strong>Important fields</strong>: <code>code</code> (unique), <code>plan</code>, <code>status</code>, "
        "<code>expires_at</code>, <code>redeemed_by</code>, <code>max_uses</code>/<code>use_count</code>, "
        "<code>bound_mac</code>.",
        "<strong>Chain</strong>: On redeem, creates/links <code>Entitlement</code>; may link "
        "<code>Payment</code> for audit; printed codes should match what users type in the portal.",
    ),
    "payments.payment": _html(
        "<strong>Role</strong>: Money-in record for a customer: amount, provider (e.g. Paystack/manual), "
        "reconciliation ids.",
        "<strong>Important fields</strong>: <code>customer</code>, <code>plan</code> (what was purchased), "
        "<code>status</code>, <code>provider_reference</code> (webhook idempotency), <code>metadata</code>.",
        "<strong>Chain</strong>: Successful payments trigger fulfillment (e.g. entitlement or voucher); "
        "ties finance to <code>Plan</code> without replacing RADIUS tables.",
    ),
    "sessions.entitlement": _html(
        "<strong>Role</strong>: Active or pending right to use the network for a plan—after payment or "
        "voucher redemption.",
        "<strong>Important fields</strong>: <code>plan</code>, <code>customer</code> or <code>voucher</code> "
        "(provenance), <code>status</code>, <code>start_at</code>/<code>end_at</code>, "
        "<code>remaining_data_bytes</code>.",
        "<strong>Chain</strong>: Authoritative quota for access; <code>Session</code> should reference it; "
        "RADIUS username mapping often aligns with entitlement lifecycle.",
    ),
    "sessions.session": _html(
        "<strong>Role</strong>: One live or closed hotspot session: user, MAC, NAS, counters, disconnect reason.",
        "<strong>Important fields</strong>: <code>session_id</code> (unique RADIUS/session key), "
        "<code>username</code>, <code>mac_address</code>, <code>nas</code>, octets/duration, "
        "<code>entitlement</code>.",
        "<strong>Chain</strong>: Updated from accounting; <code>AccountingRecord</code> may link here; "
        "drives support views and usage vs entitlement limits.",
    ),
    "sessions.accountingrecord": _html(
        "<strong>Role</strong>: Normalized snapshot of a RADIUS accounting event (interim or stop) for the app DB.",
        "<strong>Important fields</strong>: <code>event_type</code>, <code>session_id</code>, "
        "<code>username</code>, octets/duration, <code>linked_session</code>, <code>raw_payload</code>.",
        "<strong>Chain</strong>: Ingested from NAS/aggregator; updates <code>Session</code> counters and "
        "audit; complements raw <code>radacct</code> rows.",
    ),
    "radius_integration.radcheck": _html(
        "<strong>Role</strong>: FreeRADIUS <code>radcheck</code> row: authentication check (password, "
        "Cleartext-Password, etc.) for a username.",
        "<strong>Important fields</strong>: <code>username</code>, <code>attribute</code>, <code>op</code>, "
        "<code>value</code>—must match what FreeRADIUS expects.",
        "<strong>Chain</strong>: Consulted on Access-Request; out of band from Django ORM unless your "
        "integration syncs users here.",
    ),
    "radius_integration.radreply": _html(
        "<strong>Role</strong>: FreeRADIUS <code>radreply</code> row: per-user reply attributes (rate limit, "
        "Framed-IP-Address, etc.).",
        "<strong>Important fields</strong>: <code>username</code>, <code>attribute</code>, <code>value</code>.",
        "<strong>Chain</strong>: Returned on Access-Accept; should align with <code>Plan</code> / "
        "<code>SpeedProfile</code> policy for that subscriber.",
    ),
    "radius_integration.radacct": _html(
        "<strong>Role</strong>: FreeRADIUS accounting table—authoritative session accounting as seen by the NAS.",
        "<strong>Important fields</strong>: <code>acctuniqueid</code>, <code>acctsessionid</code>, "
        "<code>username</code>, <code>nasipaddress</code>, start/stop times, input/output octets, terminate cause.",
        "<strong>Chain</strong>: Populated by RADIUS Accounting-Request; may be synced or reconciled with "
        "app <code>Session</code> / <code>AccountingRecord</code>.",
    ),
    "network.site": _html(
        "<strong>Role</strong>: Physical or logical venue: groups NAS devices and optional IP hints for ops.",
        "<strong>Important fields</strong>: <code>name</code>, hotspot/management subnets, <code>is_active</code>.",
        "<strong>Chain</strong>: <code>NASDevice</code> belongs to a site; reporting and admin filters often "
        "roll up by site.",
    ),
    "network.nasdevice": _html(
        "<strong>Role</strong>: Router/hotspot gateway that speaks RADIUS to your server (IP + shared secret).",
        "<strong>Important fields</strong>: <code>site</code>, <code>ip_address</code> (unique per site), "
        "<code>secret</code> (must match NAS config), <code>shortname</code>.",
        "<strong>Chain</strong>: Linked from <code>Session</code>; identifies which edge sent accounting; "
        "pairs with <code>RadiusClient</code> metadata for client lists.",
    ),
    "network.radiusclient": _html(
        "<strong>Role</strong>: RADIUS client identity attached to a NAS—identifier + secret for the RADIUS "
        "server’s client table.",
        "<strong>Important fields</strong>: <code>nas</code>, unique <code>identifier</code>, "
        "<code>shared_secret</code>, <code>enabled</code>.",
        "<strong>Chain</strong>: Operational mirror of FreeRADIUS <code>clients</code> config; not consumed by "
        "Django RADIUS code yet, but documents which peer credentials belong to which NAS.",
    ),
    "audit.auditlog": _html(
        "<strong>Role</strong>: Append-only style record of who did what to which entity, for compliance and "
        "debugging.",
        "<strong>Important fields</strong>: <code>actor</code>, <code>action</code>, <code>target_type</code>, "
        "<code>target_id</code>, <code>details</code> (JSON), <code>ip_address</code>.",
        "<strong>Chain</strong>: Written by application code on sensitive changes; read in audits and "
        "incident response—not on the RADIUS hot path.",
    ),
    "dashboard.kpisnapshot": _html(
        "<strong>Role</strong>: Point-in-time metrics snapshot for dashboards (sessions, customers, revenue).",
        "<strong>Important fields</strong>: <code>active_sessions</code>, <code>active_customers</code>, "
        "<code>revenue_total</code>, optional <code>notes</code>.",
        "<strong>Chain</strong>: Aggregated from operational tables or jobs; used for trends, not as source "
        "of truth for billing.",
    ),
}


class EcosystemSummaryAdminMixin:
    """Injects ``ecosystem_summary`` into admin change/add form context."""

    def changeform_view(
        self,
        request: Any,
        object_id: str | None = None,
        form_url: str = "",
        extra_context: dict[str, Any] | None = None,
    ) -> Any:
        extra_context = extra_context or {}
        key = f"{self.model._meta.app_label}.{self.model._meta.model_name}"
        summary = ECOSYSTEM_SUMMARIES.get(key)
        if summary is not None:
            extra_context["ecosystem_summary"] = summary
        return super().changeform_view(request, object_id, form_url, extra_context=extra_context)
