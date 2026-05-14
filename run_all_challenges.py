#!/usr/bin/env python3
"""
Master setup and launch script for all CTF web challenges.

Sets up dependencies and runs each challenge on a predetermined port:
- Challenge 1 (Hidden Admin Panel):       http://localhost:8100
- Challenge 2 (SQL Injection Login):      http://localhost:8101
- Challenge 3 (XSS Discovery):            http://localhost:8102
- Challenge 4 (IDOR Notes API):           http://localhost:8103
- Challenge 5 (Compartmentalized Vault):  http://localhost:8104
"""

import os
import sys
import re
import subprocess
import time
from pathlib import Path


# Configuration
CHALLENGES = {
    1: {
        "name": "Hidden Admin Panel",
        "dir": "web-exploitation-challenges-1-hidden-admin-panel",
        "port": 8100,
        "type": "static",
    },
    2: {
        "name": "SQL Injection Login",
        "dir": "web-exploitation-challenges-2-sql-injection-login",
        "port": 8101,
        "type": "static",
    },
    3: {
        "name": "XSS Discovery",
        "dir": "web-exploitation-challenges-3-xss-discovery",
        "port": 8102,
        "type": "flask",
    },
    4: {
        "name": "IDOR Notes API",
        "dir": "web-exploitation-challenges-4-idor-notes-api",
        "port": 8103,
        "type": "flask",
    },
    5: {
        "name": "Compartmentalized Vault",
        "dir": "web-exploitation-challenges-5-compartmentalized-vault",
        "port": 8104,
        "type": "flask",
    },
}

BASE_DIR = Path(__file__).parent
PROCESSES = []
VENV_DIR = BASE_DIR / "venv"
PYTHON_EXECUTABLE = sys.executable


def run_command(cmd, description=""):
    """Run a command and return success status."""
    print(f"  ► {description}")
    try:
        use_shell = isinstance(cmd, str)
        result = subprocess.run(cmd, capture_output=True, text=True, shell=use_shell)
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            print(f"    ✗ Failed: {error_msg}")
            return False
        return True
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False


def get_venv_python_path():
    """Return the Python executable path inside the local virtual environment."""
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python3"


def ensure_virtualenv():
    """Create and initialize a local virtual environment if needed."""
    global PYTHON_EXECUTABLE

    venv_python = get_venv_python_path()
    if not venv_python.exists():
        print("\n🔧 Creating isolated Python environment...")
        if not run_command([sys.executable, "-m", "venv", str(VENV_DIR)], "Creating ./venv"):
            return False

    PYTHON_EXECUTABLE = str(venv_python)

    # Ensure pip tooling in the venv is available and current.
    if not run_command(
        [PYTHON_EXECUTABLE, "-m", "pip", "install", "--upgrade", "pip"],
        "Updating pip in virtual environment",
    ):
        return False

    return True


def install_dependencies():
    """Install required Python packages."""
    print("\n🔧 Installing dependencies...")
    packages = ["Flask>=2.0"]
    cmd = [PYTHON_EXECUTABLE, "-m", "pip", "install", *packages]
    return run_command(cmd, "Installing Flask")


def setup_challenge(challenge_num, config):
    """Set up a single challenge."""
    challenge_dir = BASE_DIR / config["dir"]
    requirements_file = challenge_dir / "requirements.txt"

    print(f"\n📦 Setting up Challenge {challenge_num}: {config['name']}")

    if not challenge_dir.exists():
        print(f"  ✗ Directory not found: {challenge_dir}")
        return False

    # Install requirements if they exist
    if requirements_file.exists():
        cmd = [PYTHON_EXECUTABLE, "-m", "pip", "install", "-r", str(requirements_file)]
        if not run_command(cmd, f"Installing requirements from {requirements_file.name}"):
            return False

    print(f"  ✓ Challenge {challenge_num} ready")
    return True


def start_challenge(challenge_num, config):
    """Start a challenge on its designated port."""
    challenge_dir = BASE_DIR / config["dir"]
    port = config["port"]
    challenge_type = config["type"]

    os.chdir(challenge_dir)

    if challenge_type == "static":
        # Use Python's built-in HTTP server
        cmd = [PYTHON_EXECUTABLE, "-m", "http.server", str(port)]
        label = f"Challenge {challenge_num} (Static, port {port})"
    else:  # flask
        # Modify server.py to use the right port
        server_file = challenge_dir / "server.py"
        if not server_file.exists():
            print(f"  ✗ server.py not found in {challenge_dir}")
            return False

        # Read the server.py and modify port
        with open(server_file, "r") as f:
            content = f.read()

        # Extract the filename for the subprocess label
        cmd = [PYTHON_EXECUTABLE, "server.py"]
        label = f"Challenge {challenge_num} (Flask, port {port})"

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        # Set environment variable for Flask port
        env = os.environ.copy()
        env["FLASK_PORT"] = str(port)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=challenge_dir,
        )

        PROCESSES.append((challenge_num, process, label, port))
        print(f"  ✓ {label} started (PID: {process.pid})")
        return True

    except Exception as e:
        print(f"  ✗ Failed to start: {e}")
        return False


def start_challenges_with_port_overrides():
    """Start all challenges with proper port configuration."""
    print("\n🚀 Starting all challenges...\n")

    for challenge_num, config in CHALLENGES.items():
        challenge_dir = BASE_DIR / config["dir"]
        port = config["port"]
        challenge_type = config["type"]

        print(f"  Starting Challenge {challenge_num}: {config['name']}")

        if challenge_type == "static":
            # Use Python's built-in HTTP server
            cmd = [PYTHON_EXECUTABLE, "-m", "http.server", str(port), "--directory", str(challenge_dir)]
            label = f"Challenge {challenge_num} (Static HTML, port {port})"

        else:  # flask
            # Create a wrapper script that runs the server with the right port
            server_py = challenge_dir / "server.py"
            if not server_py.exists():
                print(f"    ✗ server.py not found in {challenge_dir}")
                continue

            # Create a temporary wrapper to inject the port
            wrapper_script = challenge_dir / "_run_server_temp.py"
            with open(server_py, "r") as f:
                server_source = f.read()

            # Inject port into the app.run() call - handle both single and double quotes, and various port numbers
            # Match patterns like: port=8000, port=8001, port=8002 with or without quotes
            modified_source = re.sub(
                r'port=(\d+)',
                f'port={port}',
                server_source
            )

            with open(wrapper_script, "w") as f:
                f.write(modified_source)

            cmd = [PYTHON_EXECUTABLE, str(wrapper_script)]
            label = f"Challenge {challenge_num} (Flask, port {port})"

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            PROCESSES.append((challenge_num, process, label, port))
            print(f"    ✓ {label} started (PID: {process.pid})")
            time.sleep(0.5)  # Small delay between starts
        except Exception as e:
            print(f"    ✗ Failed to start {label}: {e}")


def print_summary():
    """Print summary of running challenges."""
    print("\n" + "=" * 70)
    print("✓ All challenges are running!")
    print("=" * 70)
    print("\n📋 Access your challenges at:\n")

    for challenge_num, config in CHALLENGES.items():
        port = config["port"]
        url = f"http://localhost:{port}"
        print(f"  Challenge {challenge_num}: {config['name']:<35} {url}")

    print("\n" + "=" * 70)
    print("Press Ctrl+C to stop all challenges")
    print("=" * 70 + "\n")


def cleanup():
    """Terminate all running processes."""
    print("\n\n🛑 Shutting down all challenges...\n")
    for challenge_num, process, label, port in PROCESSES:
        try:
            process.terminate()
            process.wait(timeout=2)
            print(f"  ✓ Stopped {label}")
        except subprocess.TimeoutExpired:
            process.kill()
            print(f"  ✓ Forced stop {label}")
        except Exception as e:
            print(f"  ✗ Error stopping {label}: {e}")


def main():
    """Main orchestration function."""
    print("\n" + "=" * 70)
    print("  CTF Web Challenges: Master Setup & Launch")
    print("=" * 70)

    try:
        # Step 0: Ensure isolated environment so package installs never hit system Python.
        if not ensure_virtualenv():
            print("\n✗ Failed to initialize virtual environment")
            return False

        # Step 1: Install dependencies
        if not install_dependencies():
            print("\n✗ Failed to install dependencies")
            return False

        # Step 2: Set up all challenges
        print("\n📦 Setting up all challenges...")
        for challenge_num, config in CHALLENGES.items():
            if not setup_challenge(challenge_num, config):
                print(f"✗ Setup failed for Challenge {challenge_num}")
                return False

        # Step 3: Start all challenges
        start_challenges_with_port_overrides()

        # Step 4: Print summary
        print_summary()

        # Step 5: Keep running until interrupted
        while True:
            time.sleep(1)
            # Check if any process has died
            for i, (num, proc, label, port) in enumerate(PROCESSES):
                if proc.poll() is not None:
                    print(f"\n⚠️  {label} died (exit code: {proc.returncode})")

    except KeyboardInterrupt:
        cleanup()
        print("✓ All challenges stopped\n")
        return True
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        cleanup()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
