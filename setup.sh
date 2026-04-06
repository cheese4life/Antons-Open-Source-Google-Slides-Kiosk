#!/bin/bash
# ── Kiosk Setup Script ──────────────────────────────────────────────────────
# Run as root (or via sudo) on a fresh Ubuntu/Debian system.
# Sets up auto-login, auto-X-start, and the kiosk environment.
# Usage: sudo bash /opt/kiosk/setup.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# SET THIS TO YOUR MACHINES USERNAME
KIOSK_USER="zadmin2"
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# SET 'kiosk' TO YOUR MACHINES NAME (might make sense to just call your machine kiosk)
KIOSK_DIR="/opt/kiosk"
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!




# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ALL CODE BELOW NOT NECESSARY TO BE CHANGED
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

echo "=== Kiosk Setup ==="

# Package Installer
echo "[1/6] Installing packages..."
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    xorg openbox chromium-browser unclutter > /dev/null

# auto-login on startup
echo "[2/6] Configuring auto-login on tty1..."
mkdir -p /etc/systemd/system/getty@tty1.service.d
cat > /etc/systemd/system/getty@tty1.service.d/autologin.conf << EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin ${KIOSK_USER} --noclear %I \$TERM
EOF
systemctl daemon-reload

# Auto start X on login (tty1 only)
echo "[3/6] Configuring auto-start X..."
BASH_PROFILE="/home/${KIOSK_USER}/.bash_profile"
STARTX_LINE='[[ -z "$DISPLAY" && "$(tty)" == "/dev/tty1" ]] && exec startx /opt/kiosk/xinitrc -- -nocursor'

# Add startx line if not already present
if ! grep -qF "/opt/kiosk/xinitrc" "$BASH_PROFILE" 2>/dev/null; then
    echo "$STARTX_LINE" >> "$BASH_PROFILE"
    chown "${KIOSK_USER}:${KIOSK_USER}" "$BASH_PROFILE"
fi

# Create xinitrc 
echo "[4/6] Creating xinitrc..."
cat > "${KIOSK_DIR}/xinitrc" << 'XINITRC'
#!/bin/sh

# Disable screen blanking and power management
xset s off
xset s noblank
xset -dpms

# Hide mouse cursor after 1 second of inactivity
unclutter -idle 1 -root &

# Start openbox (lightweight window manager — needed for proper fullscreen)
openbox &

# Give openbox a moment to start
sleep 2

# Launch the kiosk Python script
exec /usr/bin/python3 /opt/kiosk/kiosk.py
XINITRC
chmod +x "${KIOSK_DIR}/xinitrc"
chown "${KIOSK_USER}:${KIOSK_USER}" "${KIOSK_DIR}/xinitrc"

# Disable screen blanking in console 
echo "[5/6] Disabling console blanking..."
# Prevent kernel console blanking
if ! grep -q "consoleblank=0" /etc/default/grub 2>/dev/null; then
    sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="\(.*\)"/GRUB_CMDLINE_LINUX_DEFAULT="\1 consoleblank=0"/' /etc/default/grub
    update-grub
fi

# setting up graphical
echo "[6/6] Ensuring graphical target..."
systemctl set-default graphical.target

echo ""
echo "=== Setup complete! ==="
echo "Reboot the machine to start the kiosk:"
echo "  sudo reboot"
echo ""
