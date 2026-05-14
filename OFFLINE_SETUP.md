Offline setup instructions

1) On an internet-connected Linux machine (clone the repo or copy it):

```bash
cd /path/to/ctfchallenges
./scripts/prepare_wheels.sh $(pwd)
# This creates a 'wheels/' directory packed with required .whl files
```

2) Copy the entire `wheels/` directory to the Pi (USB stick, scp, etc.) and place it at the repository root so the path is `./wheels`.

3) On the Pi (no internet needed):

```bash
# Ensure Python3 and venv are available on the Pi
sudo apt install python3 python3-venv   # if apt packages are already available locally

# From the repo root on the Pi
python3 run_all_challenges.py
```

The launcher will detect `./wheels` and pip-install using `--no-index --find-links ./wheels`.

Notes:
- If you need system packages (.deb), use `apt-get download` on an internet host and transfer .deb files to the Pi. Installing .deb may require handling dependencies; consider using `apt-offline` for complex setups.
- For reproducibility, run `./scripts/prepare_wheels.sh` on the same Python version as the target Pi.
