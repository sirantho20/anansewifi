# Walled garden: allow HTTPS to the public Ananse portal and Paystack (*.paystack.com / *.paystack.co)
# before Hotspot login (plan purchase redirects to hosted checkout).
#
# Prerequisites (see config.txt §14–15): device-mode proxy=yes (enable_proxy_device_mode.rsc + reboot),
# /interface bridge settings set [find name=bridge-main] use-ip-firewall=yes, working DNS for guests.
#
# Apply: upload to the router Files, then:
#   /import file-name=hotspot_external_portal.rsc
# Or paste into a RouterOS terminal.
#
# Idempotent: each :if skips if that dst-host entry already exists.

:if ([:len [/ip hotspot walled-garden ip find dst-host="anansewifi.shrt.fit"]] = 0) do={
  /ip hotspot walled-garden ip add dst-host=anansewifi.shrt.fit comment="Ananse external portal (HTTPS pre-login)"
}

:if ([:len [/ip hotspot walled-garden ip find dst-host="paystack.com"]] = 0) do={
  /ip hotspot walled-garden ip add dst-host=paystack.com comment="Paystack apex .com (HTTPS pre-login)"
}

:if ([:len [/ip hotspot walled-garden ip find dst-host="*.paystack.com"]] = 0) do={
  /ip hotspot walled-garden ip add dst-host="*.paystack.com" comment="Paystack subdomains .com (HTTPS pre-login)"
}

:if ([:len [/ip hotspot walled-garden ip find dst-host="paystack.co"]] = 0) do={
  /ip hotspot walled-garden ip add dst-host=paystack.co comment="Paystack apex .co (HTTPS pre-login)"
}

:if ([:len [/ip hotspot walled-garden ip find dst-host="*.paystack.co"]] = 0) do={
  /ip hotspot walled-garden ip add dst-host="*.paystack.co" comment="Paystack subdomains .co api/js etc (HTTPS pre-login)"
}
