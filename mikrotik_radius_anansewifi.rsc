# Point MikroTik Hotspot RADIUS to your Ananse WiFi FreeRADIUS (UDP 1812/1813 on the VPS).
# The public HTTPS name (e.g. anansewifi.shrt.fit) is often on Cloudflare proxy — that does not carry UDP.
# Set radAddr to your VPS public IP or a DNS-only (grey cloud) A record, not a Cloudflare-proxied name.
# Secret must match RADIUS_CLIENT_SECRET (and the optional RADIUS_NAS client secret) in server .env.
#
# Apply: copy to the router (Files) or paste into a terminal, then:
#   /import file-name=mikrotik_radius_anansewifi.rsc
#
# Before import, replace PLACEHOLDERS below, or set :local variables in Winbox/SSH before pasting the /radius and /ip lines.
#
# Verify from the router: /ping  address=<radAddr>  (must route over WAN, not the hotspot lab with no default route)
# Test auth: on the server, radtest <user> <pass> <host> 0 <secret>

# Production VPS (UDP 1812/1813). Override if RADIUS moves. HTTPS stays on anansewifi.shrt.fit (Cloudflare); RADIUS uses this IP.
:local radAddr "77.237.238.58"
:local radSec "ananse-radius-secret"
:local profileName "cp-main"

/radius add name=ananse-anansewifi address=$radAddr secret=$radSec service=hotspot,login protocol=udp authentication-port=1812 accounting-port=1813 timeout=5s comment="Ananse WiFi"

/ip hotspot profile set [find name=$profileName] use-radius=yes

# If you have multiple RADIUS entries, you may need to assign this server explicitly; check with:
#   /ip hotspot profile print where name=cp-main
