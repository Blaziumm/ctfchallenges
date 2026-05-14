#!/usr/bin/env bash
set -euo pipefail

# pi_setup.sh
# Usage: sudo ./pi_setup.sh [interface]
# Default interface: eth0

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run with sudo. Example: sudo ./pi_setup.sh"
  exit 1
fi

INTERFACE="${1:-eth0}"
STATIC_IP="192.168.1.5/24"
ROUTERS="192.168.1.1"
DNS="192.168.1.1 8.8.8.8"

DHCPCD_CONF="/etc/dhcpcd.conf"
BACKUP="${DHCPCD_CONF}.ctf_bak_$(date +%s)"

echo "Backing up ${DHCPCD_CONF} -> ${BACKUP}"
cp -a "${DHCPCD_CONF}" "${BACKUP}"

echo "Removing any existing CTFCHALLENGES block in ${DHCPCD_CONF}"
sed -i '/# CTFCHALLENGES-BEGIN/,/# CTFCHALLENGES-END/d' "${DHCPCD_CONF}" || true

cat >> "${DHCPCD_CONF}" <<EOF
# CTFCHALLENGES-BEGIN
interface ${INTERFACE}
static ip_address=${STATIC_IP}
static routers=${ROUTERS}
static domain_name_servers=${DNS}
# CTFCHALLENGES-END
EOF

echo "Wrote static IP configuration for ${INTERFACE}: ${STATIC_IP}"

# Create a systemd service that runs the challenges on boot.
SERVICE_PATH="/etc/systemd/system/ctfchallenges.service"
TARGET_USER="${SUDO_USER:-pi}"

echo "Installing systemd service at ${SERVICE_PATH} (runs as ${TARGET_USER})"
cat > "${SERVICE_PATH}" <<SERVICE_EOF
[Unit]
Description=CTF Challenges Runner
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${TARGET_USER}
WorkingDirectory=${REPO_DIR}
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/env python3 ${REPO_DIR}/run_all_challenges.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE_EOF

echo "Reloading systemd and enabling service"
systemctl daemon-reload
systemctl enable ctfchallenges.service

echo "Starting service now (may fail if network change drops connectivity)"
systemctl start ctfchallenges.service || echo "Service start returned non-zero; check 'journalctl -u ctfchallenges'"

echo "IMPORTANT: Changing the Pi's IP may disconnect your SSH session if run remotely over SSH."
echo "If you are connected over SSH, consider running this from local console or expect to reconnect to 192.168.1.5."

echo "Setup complete. Static IP: ${STATIC_IP} on ${INTERFACE}."
echo "Service: systemctl status ctfchallenges"

exit 0
#!/usr/bin/env bash

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATIC_IP="192.168.1.5"
PREFIX="24"
GATEWAY="192.168.1.1"
DNS_SERVERS="1.1.1.1,8.8.8.8"
INTERFACE="eth0"
SERVICE_USER="${SUDO_USER:-pi}"
PYTHON_BIN="$(command -v python3)"

usage() {
  cat <<EOF
Usage: sudo ./pi_setup.sh [options]

Options:
  --repo-dir PATH     Path to this repository (defaults to the script location)
  --interface NAME    Network interface to configure (default: eth0)
  --ip ADDRESS        Static IP address (default: 192.168.1.5)
  --gateway ADDRESS   Gateway address (default: 192.168.1.1)
  --dns LIST          Comma-separated DNS servers (default: 1.1.1.1,8.8.8.8)
  --user NAME         User that should run the boot service (default: sudo user or pi)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-dir)
      REPO_DIR="$2"
      shift 2
      ;;
    --interface)
      INTERFACE="$2"
      shift 2
      ;;
    --ip)
      STATIC_IP="$2"
      shift 2
      ;;
    --gateway)
      GATEWAY="$2"
      shift 2
      ;;
    --dns)
      DNS_SERVERS="$2"
      shift 2
      ;;
    --user)
      SERVICE_USER="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ $EUID -ne 0 ]]; then
  echo "Run this script with sudo or as root." >&2
  exit 1
fi

if [[ ! -d "$REPO_DIR" ]]; then
  echo "Repository directory not found: $REPO_DIR" >&2
  exit 1
fi

if [[ ! -f "$REPO_DIR/run_all_challenges.py" ]]; then
  echo "run_all_challenges.py was not found in $REPO_DIR" >&2
  exit 1
fi

if ! id "$SERVICE_USER" >/dev/null 2>&1; then
  echo "User not found: $SERVICE_USER" >&2
  exit 1
fi

if ! ip link show "$INTERFACE" >/dev/null 2>&1; then
  echo "Network interface not found: $INTERFACE" >&2
  exit 1
fi

configure_networkmanager() {
  local connection
  local dns_text="${DNS_SERVERS//,/ }"

  connection="$(nmcli -t -f NAME,DEVICE connection show --active | awk -F: -v iface="$INTERFACE" '$2==iface {print $1; exit}')"
  if [[ -z "$connection" ]]; then
    connection="$(nmcli -t -f NAME,DEVICE connection show | awk -F: -v iface="$INTERFACE" '$2==iface {print $1; exit}')"
  fi

  if [[ -z "$connection" ]]; then
    return 1
  fi

  echo "Configuring NetworkManager connection: $connection"
  nmcli connection modify "$connection" \
    ipv4.addresses "${STATIC_IP}/${PREFIX}" \
    ipv4.gateway "$GATEWAY" \
    ipv4.dns "$dns_text" \
    ipv4.method manual \
    ipv6.method ignore

  nmcli connection up "$connection" || true
}

configure_dhcpcd() {
  local config_file="/etc/dhcpcd.conf"
  local marker="# CTF challenges static IP"
  local dns_text="${DNS_SERVERS//,/ }"

  if ! grep -qF "$marker" "$config_file"; then
    cat <<EOF >> "$config_file"

$marker
interface $INTERFACE
static ip_address=${STATIC_IP}/${PREFIX}
static routers=${GATEWAY}
static domain_name_servers=${dns_text}
EOF
  fi

  if systemctl is-active --quiet dhcpcd 2>/dev/null; then
    systemctl restart dhcpcd
  elif service dhcpcd restart >/dev/null 2>&1; then
    :
  fi
}

echo "Setting static IP on $INTERFACE to ${STATIC_IP}/${PREFIX}"
if command -v nmcli >/dev/null 2>&1; then
  if ! configure_networkmanager; then
    echo "NetworkManager was not able to manage $INTERFACE, trying dhcpcd..."
    configure_dhcpcd
  fi
elif [[ -f /etc/dhcpcd.conf ]]; then
  configure_dhcpcd
else
  echo "Neither nmcli nor dhcpcd is available for network configuration." >&2
  exit 1
fi

service_file="/etc/systemd/system/ctfchallenges.service"

cat > "$service_file" <<EOF
[Unit]
Description=CTF Challenges launcher
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$REPO_DIR
ExecStart=$PYTHON_BIN $REPO_DIR/run_all_challenges.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ctfchallenges.service
systemctl restart ctfchallenges.service

echo
echo "Done."
echo "Static IP: ${STATIC_IP}/${PREFIX} on ${INTERFACE}"
echo "Service: ctfchallenges.service"
echo "Check status with: systemctl status ctfchallenges.service"