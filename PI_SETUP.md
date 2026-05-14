# Raspberry Pi Lite Setup

This repository includes a setup script for Raspberry Pi OS Lite that:

- configures a static LAN address of `192.168.1.5`
- installs a systemd service so the challenge launcher starts on boot
- uses `run_all_challenges.py` to bring up all five challenges after the Pi powers on

## Usage

Run this from the repository root on the Pi:

```bash
sudo ./pi_setup.sh
```

If you are using Wi-Fi instead of Ethernet, pass the interface explicitly:

```bash
sudo ./pi_setup.sh --interface wlan0
```

You can also override the IP settings if your network is not on `192.168.1.0/24`:

```bash
sudo ./pi_setup.sh --ip 192.168.1.5 --gateway 192.168.1.1 --dns 1.1.1.1,8.8.8.8
```

## What It Installs

- Static IP configuration through NetworkManager when available, otherwise `dhcpcd`
- `ctfchallenges.service` in systemd
- Boot-time launch of `run_all_challenges.py`

## Verification

After the script finishes, check:

```bash
hostname -I
systemctl status ctfchallenges.service
```

If `hostname -I` is still empty, the Pi is not receiving an address from the configured interface, which usually means the wrong interface was selected or the network settings need to match the router's subnet.