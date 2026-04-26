# Enable /ip proxy in device-mode so Hotspot walled-garden (captive.apple.com, etc.) is not
# left "inactivated, not allowed by device-mode" on mode=home.
#
# Apply: upload to the router Files, then in terminal: /import file-name=enable_proxy_device_mode.rsc
# Or paste these two lines into a RouterOS terminal (Winbox or SSH with a real TTY).
#
# After running, the router will require confirmation: power off, or press Reset/Mode within 5 minutes
# (see on-screen message). Then it reboots. Without that step, the change is discarded.
#
# After reboot, verify:
#   /ip hotspot walled-garden print  (entries should not show the "inactivated, not allowed by device-mode" note)
#   /ip proxy print
#
# If update fails with "too many attempts", power-cycle to reset device-mode attempt-count, then re-import.
#
# Reference: https://help.mikrotik.com/docs/spaces/ROS/pages/93749258/Device-mode

/system device-mode update proxy=yes
