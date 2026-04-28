from __future__ import annotations

from typing import Any

from django.db import models

from core.models import BaseModel


class BillingType(models.TextChoices):
    VOUCHER = "voucher", "Voucher"
    DIRECT = "direct", "Direct"
    MANUAL = "manual", "Manual"


class QuotaType(models.TextChoices):
    DURATION = "duration", "Duration"
    DATA = "data", "Data"
    DURATION_AND_DATA = "duration_and_data", "Duration And Data"
    UNLIMITED = "unlimited", "Unlimited"


class SpeedProfile(BaseModel):
    name = models.CharField(max_length=64, unique=True)
    up_rate_kbps = models.PositiveIntegerField(default=1024)
    down_rate_kbps = models.PositiveIntegerField(default=1024)
    mikrotik_rate_limit = models.CharField(max_length=128, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.up_rate_kbps}/{self.down_rate_kbps} kbps)"


class Plan(BaseModel):
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    billing_type = models.CharField(
        max_length=16,
        choices=BillingType.choices,
        default=BillingType.VOUCHER,
    )
    quota_type = models.CharField(
        max_length=20,
        choices=QuotaType.choices,
        default=QuotaType.DURATION,
    )
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    data_bytes = models.BigIntegerField(null=True, blank=True)
    speed_profile = models.ForeignKey(
        SpeedProfile,
        on_delete=models.PROTECT,
        related_name="plans",
        null=True,
        blank=True,
    )
    concurrent_device_limit = models.PositiveSmallIntegerField(default=1)
    idle_timeout_seconds = models.PositiveIntegerField(default=600)
    session_timeout_seconds = models.PositiveIntegerField(default=3600)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(
        default=False,
        help_text="Highlight this plan on the public plans page (e.g. POPULAR ribbon).",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.id})"

    @staticmethod
    def _format_duration_minutes(minutes: int) -> str:
        if minutes <= 0:
            return ""
        if minutes % 1440 == 0:
            d = minutes // 1440
            return f"{d} day{'s' if d != 1 else ''}"
        if minutes % 60 == 0:
            h = minutes // 60
            return f"{h} hour{'s' if h != 1 else ''}"
        return f"{minutes} min"

    @staticmethod
    def _format_data_bytes(num_bytes: int) -> str:
        if num_bytes >= 1024**3:
            gb = num_bytes / (1024**3)
            text = f"{gb:.1f}".rstrip("0").rstrip(".")
            return f"{text} GB data"
        mb = num_bytes / (1024**2)
        text = f"{mb:.0f}" if mb >= 10 else f"{mb:.1f}".rstrip("0").rstrip(".")
        return f"{text} MB data"

    def human_duration_badge_label(self) -> str | None:
        if self.duration_minutes is None:
            return None
        return self._format_duration_minutes(int(self.duration_minutes)).title()

    def human_data_badge_label(self) -> str | None:
        if self.data_bytes is None:
            return None
        s = self._format_data_bytes(int(self.data_bytes))
        # "5 GB data" -> "5 GB Data"
        if s.endswith(" data"):
            return s[:-5] + " Data"
        return s

    def speed_badge_label(self) -> str | None:
        sp = self.speed_profile
        if sp is None:
            return None
        down_mbps = sp.down_rate_kbps / 1024
        if down_mbps >= 1:
            speed = f"{down_mbps:.0f} Mbps" if down_mbps == int(down_mbps) else f"{down_mbps:.1f} Mbps"
        else:
            speed = f"{sp.down_rate_kbps} kbps"
        return f"{sp.name} ({speed})"

    @staticmethod
    def _format_seconds_duration(seconds: int) -> str:
        if seconds <= 0:
            return "—"
        minutes = max(1, (seconds + 59) // 60)
        return Plan._format_duration_minutes(minutes).title()

    def plan_detail_lines(self) -> list[dict[str, str]]:
        """Technical limits for collapsible plan details."""
        return [
            {"label": "Quota type", "value": self.get_quota_type_display()},
            {
                "label": "Session timeout",
                "value": f"{self._format_seconds_duration(int(self.session_timeout_seconds))} "
                f"({self.session_timeout_seconds}s)",
            },
            {
                "label": "Idle timeout",
                "value": f"{self._format_seconds_duration(int(self.idle_timeout_seconds))} "
                f"({self.idle_timeout_seconds}s)",
            },
        ]

    _BADGE_FA: dict[str, str] = {
        "clock": "fa-solid fa-clock",
        "database": "fa-solid fa-database",
        "infinity": "fa-solid fa-infinity",
        "gauge-high": "fa-solid fa-gauge-high",
        "tag": "fa-solid fa-tag",
        "mobile-screen": "fa-solid fa-mobile-screen",
    }

    def quota_summary_badges(self) -> list[dict[str, Any]]:
        """Badges for the plan card; each dict has icon_classes (Font Awesome) and label."""
        raw: list[dict[str, str]] = []
        qt = self.quota_type

        if qt == QuotaType.DURATION:
            label = self.human_duration_badge_label()
            if label:
                raw.append({"icon": "clock", "label": label})
        elif qt == QuotaType.DATA:
            label = self.human_data_badge_label()
            if label:
                raw.append({"icon": "database", "label": label})
        elif qt == QuotaType.DURATION_AND_DATA:
            dlabel = self.human_duration_badge_label()
            if dlabel:
                raw.append({"icon": "clock", "label": dlabel})
            dblabel = self.human_data_badge_label()
            if dblabel:
                raw.append({"icon": "database", "label": dblabel})
        elif qt == QuotaType.UNLIMITED:
            raw.append({"icon": "infinity", "label": "Unlimited data"})
            dlabel = self.human_duration_badge_label()
            if dlabel:
                raw.append({"icon": "clock", "label": dlabel})

        raw.append({"icon": "tag", "label": self.get_billing_type_display()})
        if self.concurrent_device_limit > 1:
            n = self.concurrent_device_limit
            raw.append({"icon": "mobile-screen", "label": f"Up to {n} devices"})

        out: list[dict[str, Any]] = []
        for row in raw:
            icon = row["icon"]
            fa = self._BADGE_FA.get(icon, "fa-solid fa-circle")
            out.append({**row, "icon_classes": fa})
        return out

    def purchase_validity_summary(self) -> str:
        """Quota-only validity text for purchase confirmation (mirrors quota_summary_badges, no billing/devices)."""
        parts: list[str] = []
        qt = self.quota_type

        if qt == QuotaType.DURATION:
            label = self.human_duration_badge_label()
            if label:
                parts.append(label)
        elif qt == QuotaType.DATA:
            label = self.human_data_badge_label()
            if label:
                parts.append(label)
        elif qt == QuotaType.DURATION_AND_DATA:
            dlabel = self.human_duration_badge_label()
            if dlabel:
                parts.append(dlabel)
            dblabel = self.human_data_badge_label()
            if dblabel:
                parts.append(dblabel)
        elif qt == QuotaType.UNLIMITED:
            parts.append("Unlimited data")
            dlabel = self.human_duration_badge_label()
            if dlabel:
                parts.append(dlabel)

        return " · ".join(parts)

    def card_corner_icon(self) -> tuple[str, str]:
        """
        Font Awesome icon name (no fa- prefix) and style variant:
        'solid' or 'accent_box' (accent-tinted box) or 'gradient' (featured).
        """
        if self.is_featured:
            return "rocket", "gradient"
        if self.quota_type == QuotaType.UNLIMITED:
            return "infinity", "accent_box"
        if self.quota_type == QuotaType.DATA:
            return "database", "solid"
        if self.quota_type == QuotaType.DURATION_AND_DATA:
            return "gauge-high", "solid"
        if self.quota_type == QuotaType.DURATION:
            return "clock", "solid"
        return "wifi", "solid"

    @property
    def corner_icon_name(self) -> str:
        return self.card_corner_icon()[0]

    @property
    def corner_icon_variant(self) -> str:
        return self.card_corner_icon()[1]

