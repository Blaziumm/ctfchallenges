# CTF Challenges - Running All Services

## Overview
The `run_all_challenges.py` script automatically runs all five web exploitation challenges on predetermined ports.

## Quick Start

```bash
python3 run_all_challenges.py
```

The script will:
1. ✓ Verify each challenge directory exists
2. ✓ Start all challenges on different ports
3. ✓ Display access URLs

## Challenge Ports

| Challenge | URL | Port |
|-----------|-----|------|
| 1. Hidden Admin Panel | http://localhost:8100 | 8100 |
| 2. SQL Injection Login | http://localhost:8101 | 8101 |
| 3. XSS Discovery | http://localhost:8102 | 8102 |
| 4. IDOR Notes API | http://localhost:8103 | 8103 |
| 5. Compartmentalized Vault | http://localhost:8104 | 8104 |

## How It Works

The master script:
- Uses Python's built-in `http.server` for the static challenges
- Runs the API challenges with stdlib HTTP handlers
- Keeps all services in-process and shuts them down cleanly on Ctrl+C

## Stopping Services

Press **Ctrl+C** in the terminal where the script is running to cleanly shut down all challenges.

## Manual Control

If you need to stop services manually:

```bash
# Kill all challenge processes
killall -9 python3
```

## Notes

- Each challenge runs independently and doesn't affect others
- All services are accessible from `localhost` in development
- The wrapper scripts (`_run_server_temp.py`) are created dynamically in each challenge directory
- To run individual challenges, see the README in each challenge folder

## Hosting Under A CTFd Domain Path

If the CTFd site is already being served through a reverse proxy, mount each challenge under a path on that same domain and proxy it to the local ports above.

Example Nginx locations:

```nginx
location /challenge-1/ { proxy_pass http://127.0.0.1:8100/; }
location /challenge-2/ { proxy_pass http://127.0.0.1:8101/; }
location /challenge-3/ { proxy_pass http://127.0.0.1:8102/; }
location /challenge-4/ { proxy_pass http://127.0.0.1:8103/; }
location /challenge-5/ { proxy_pass http://127.0.0.1:8104/; }
```

The trailing slash matters because it strips the path prefix before forwarding to the local challenge server. The IDOR and vault challenges already use relative asset/API URLs, so they work correctly when mounted this way.

## Raspberry Pi Lite Boot Setup

If you want the challenges to come up automatically on a Raspberry Pi Lite install with a static LAN address, use the helper script in [PI_SETUP.md](PI_SETUP.md).

The script configures `192.168.1.5` by default and installs a `ctfchallenges.service` systemd unit that starts the challenge launcher on boot.
