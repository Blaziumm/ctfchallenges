#!/usr/bin/env bash
set -euo pipefail

# prepare_wheels.sh
# Run on an internet-connected machine to collect Python wheels for offline installs.
# Usage: ./prepare_wheels.sh /path/to/ctf-repo

REPO_DIR="${1:-$(pwd)}"
WHEEL_DIR="$REPO_DIR/wheels"

echo "Saving wheels into: $WHEEL_DIR"
mkdir -p "$WHEEL_DIR"

echo "Downloading top-level runtime wheels (Flask)..."
python3 -m pip download "Flask>=2.0" -d "$WHEEL_DIR"

echo "Searching for requirements.txt files and downloading their wheels..."
while IFS= read -r req; do
  echo "  -> $req"
  python3 -m pip download -r "$req" -d "$WHEEL_DIR"
done < <(find "$REPO_DIR" -type f -name requirements.txt)

echo "All wheels downloaded to $WHEEL_DIR"
echo "Copy this 'wheels' directory to the Pi (e.g. via USB) and place it at the repository root."

exit 0
