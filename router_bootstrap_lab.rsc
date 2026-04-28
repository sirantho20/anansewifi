# Ananse WiFi lab bootstrap — dual WAN (ether1 primary, ether2 backup), ether3 = 192.168.20.0/24,
# bridge-main (ether4+ether5) = 192.168.10.0/24 + Hotspot.
# Upload login.html to flash/hotspot/ before or after; profile expects html-directory=flash/hotspot
#
#   /import file-name=router_bootstrap_lab.rsc

# ---- 1) bridge-main + LAN membership (before port moves) ----
:if ([:len [/interface bridge find name=bridge-main]] = 0) do={
  /interface bridge add name=bridge-main protocol-mode=rstp comment="Ananse main LAN + Hotspot"
}
:if ([:len [/interface list member find where list=LAN and interface=bridge-main]] = 0) do={
  /interface list member add list=LAN interface=bridge-main
}
:if ([:len [/interface list member find where list=LAN and interface=ether3]] = 0) do={
  /interface list member add list=LAN interface=ether3
}

# ---- 2) LAN addresses + pools + DHCP ----
:if ([:len [/ip address find where address=192.168.20.1/24 and interface=ether3]] = 0) do={
  /ip address add address=192.168.20.1/24 interface=ether3 comment="Ananse backup LAN"
}
:if ([:len [/ip address find where address=192.168.10.1/24 and interface=bridge-main]] = 0) do={
  /ip address add address=192.168.10.1/24 interface=bridge-main comment="Ananse main LAN / Hotspot"
}

:if ([:len [/ip pool find name=ananse-pool-main]] = 0) do={
  /ip pool add name=ananse-pool-main ranges=192.168.10.10-192.168.10.254
}
:if ([:len [/ip pool find name=ananse-pool-backup]] = 0) do={
  /ip pool add name=ananse-pool-backup ranges=192.168.20.10-192.168.20.254
}

:if ([:len [/ip dhcp-server find name=dhcp-main]] = 0) do={
  /ip dhcp-server add name=dhcp-main interface=bridge-main address-pool=ananse-pool-main lease-time=30m disabled=no
}
:if ([:len [/ip dhcp-server find name=dhcp-backup]] = 0) do={
  /ip dhcp-server add name=dhcp-backup interface=ether3 address-pool=ananse-pool-backup lease-time=30m disabled=no
}

:if ([:len [/ip dhcp-server network find address=192.168.10.0/24]] = 0) do={
  /ip dhcp-server network add address=192.168.10.0/24 gateway=192.168.10.1 dns-server=192.168.10.1 comment="main LAN"
}
:if ([:len [/ip dhcp-server network find address=192.168.20.0/24]] = 0) do={
  /ip dhcp-server network add address=192.168.20.0/24 gateway=192.168.20.1 dns-server=192.168.20.1 comment="backup LAN ether3"
}

# ---- 3) Stop defconf DHCP (frees bridge for port surgery) ----
:if ([:len [/ip dhcp-server find name=defconf]] > 0) do={
  /ip dhcp-server set [find name=defconf] disabled=yes
}

# ---- 4) Remove LAN ports from defconf bridge; attach ether4/5 to bridge-main ----
:if ([:len [/interface bridge port find interface=ether2]] > 0) do={
  /interface bridge port remove [find interface=ether2]
}
:if ([:len [/interface bridge port find interface=ether3]] > 0) do={
  /interface bridge port remove [find interface=ether3]
}
:if ([:len [/interface bridge port find interface=ether4]] > 0) do={
  /interface bridge port remove [find interface=ether4]
}
:if ([:len [/interface bridge port find interface=ether5]] > 0) do={
  /interface bridge port remove [find interface=ether5]
}

:if ([:len [/interface bridge port find where bridge=bridge-main and interface=ether4]] = 0) do={
  /interface bridge port add bridge=bridge-main interface=ether4 hw=yes
}
:if ([:len [/interface bridge port find where bridge=bridge-main and interface=ether5]] = 0) do={
  /interface bridge port add bridge=bridge-main interface=ether5 hw=yes
}

# ---- 5) ether2 = backup WAN ----
:if ([:len [/interface list member find where list=WAN and interface=ether2]] = 0) do={
  /interface list member add list=WAN interface=ether2
}
:if ([:len [/ip dhcp-client find interface=ether2]] = 0) do={
  /ip dhcp-client add interface=ether2 add-default-route=yes default-route-distance=2 use-peer-dns=yes disabled=no comment="backup WAN"
}

:if ([:len [/ip dhcp-client find interface=ether1]] > 0) do={
  /ip dhcp-client set [find interface=ether1] default-route-distance=1 add-default-route=yes
}

# ---- 6) Remove legacy 192.168.88.1 from defconf bridge ----
:if ([:len [/ip address find address=192.168.88.1/24]] > 0) do={
  /ip address remove [find address=192.168.88.1/24]
}

# ---- 7) Bridge IP firewall for Hotspot (global bridge setting on this platform) ----
/interface bridge settings set use-ip-firewall=yes

# ---- 8) Forward: main LAN may not use backup WAN ----
:if ([:len [/ip firewall filter find comment="ananse-mainLAN-no-backup-WAN"]] = 0) do={
  /ip firewall filter add chain=forward action=drop src-address=192.168.10.0/24 out-interface=ether2 comment="ananse-mainLAN-no-backup-WAN" place-before=0
}

# ---- 9) DNS for Hotspot clients ----
/ip dns set allow-remote-requests=yes servers=8.8.8.8,1.1.1.1
:if ([:len [/ip dns static find name=login.hotspot]] = 0) do={
  /ip dns static add name=login.hotspot address=192.168.10.1 comment="Hotspot captive DNS"
}

# ---- 10) RADIUS + Hotspot (no name= on /radius add for ROS 7.19) ----
:if ([:len [/radius find address=77.237.238.58 service=hotspot]] = 0) do={
  /radius add address=77.237.238.58 secret=ananse-radius-secret service=hotspot protocol=udp authentication-port=1812 accounting-port=1813 timeout=5s
}

:if ([:len [/ip hotspot profile find name=cp-main]] = 0) do={
  /ip hotspot profile add name=cp-main hotspot-address=192.168.10.1 dns-name=login.hotspot html-directory=flash/hotspot login-by=cookie,http-chap,http-pap http-cookie-lifetime=3d ssl-certificate=none use-radius=yes
} else={
  /ip hotspot profile set [find name=cp-main] use-radius=yes dns-name=login.hotspot html-directory=flash/hotspot hotspot-address=192.168.10.1 ssl-certificate=none
}

:if ([:len [/ip hotspot find name=hotspot-main]] = 0) do={
  /ip hotspot add name=hotspot-main interface=bridge-main profile=cp-main address-pool=ananse-pool-main disabled=no
}

# ---- 11) Walled garden: HTTPS to public portal (login.html redirect) before auth ----
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

:put "router_bootstrap_lab: done. If walled-garden inactivated, import enable_proxy_device_mode.rsc + confirm reboot."
