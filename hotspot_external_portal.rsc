# Walled garden: allow HTTPS to the public Ananse portal before Hotspot login.
#
# Prerequisites (see config.txt §14): device-mode proxy=yes (enable_proxy_device_mode.rsc + reboot),
# /interface bridge settings set [find name=bridge-main] use-ip-firewall=yes, working DNS for guests.
#
# Apply: upload to the router Files, then:
#   /import file-name=hotspot_external_portal.rsc
# Or paste the :if block into a RouterOS terminal.
#
# If this dst-host is already present, the script does nothing (idempotent).

:if ([:len [/ip hotspot walled-garden ip find dst-host="anansewifi.shrt.fit"]] = 0) do={
  /ip hotspot walled-garden ip add dst-host=anansewifi.shrt.fit comment="Ananse external portal (HTTPS pre-login)"
}
