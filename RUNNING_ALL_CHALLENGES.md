# CTF Challenges - Running All Services

## Overview
The `run_all_challenges.py` script automatically sets up and runs all five web exploitation challenges on predetermined ports.

## Quick Start

```bash
python3 run_all_challenges.py
```

The script will:
1. ✓ Install all required dependencies (Flask)
2. ✓ Set up each challenge
3. ✓ Start all challenges on different ports
4. ✓ Display access URLs

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
- Installs Flask and other dependencies
- For static challenges (1 & 2): Uses Python's built-in `http.server`
- For Flask challenges (3, 4 & 5): 
  - Creates temporary wrapper scripts with port numbers injected
  - Uses regex to replace original port numbers with predetermined ports
- Runs all services as background processes
- Monitors for process failures
- Gracefully stops all services on Ctrl+C

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
