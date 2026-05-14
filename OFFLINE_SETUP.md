Offline setup instructions

The current repo is self-contained and does not need `venv`, Flask, or downloaded wheels to run.

If you already copied an older archive that contains `wheels/`, it is safe to leave it in place, but it is no longer required.

1) On an internet-connected Linux machine (clone the repo or copy it):

```bash
cd /path/to/ctfchallenges
# No preparation step is required for runtime.
```

2) Copy the repository folder to the Pi (USB stick, scp, etc.).

3) On the Pi (no internet needed):

```bash
# Ensure Python3 and venv are available on the Pi
sudo apt install python3 python3-venv   # if apt packages are already available locally

# From the repo root on the Pi
python3 run_all_challenges.py
```bash
cd /path/to/ctfchallenges
python3 run_all_challenges.py
```

Notes:
- The launcher now uses only the Python standard library.
- If you want, you can delete the `wheels/` directory from older archives after updating to this version.
