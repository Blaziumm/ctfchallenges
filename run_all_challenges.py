#!/usr/bin/env python3
"""
Master launcher for all CTF web challenges.

This version is fully offline and stdlib-only:
- No virtualenv is required.
- No third-party Python packages are required.
- Challenges 1, 2, and 3 are served as static files.
- Challenges 4 and 5 run as small stdlib HTTP API servers.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


BASE_DIR = Path(__file__).parent.resolve()
PROCESSES = []

CHALLENGES = {
    1: {"name": "Hidden Admin Panel", "dir": "web-exploitation-challenges-1-hidden-admin-panel", "port": 8100, "kind": "static"},
    2: {"name": "SQL Injection Login", "dir": "web-exploitation-challenges-2-sql-injection-login", "port": 8101, "kind": "static"},
    3: {"name": "XSS Discovery", "dir": "web-exploitation-challenges-3-xss-discovery", "port": 8102, "kind": "static"},
    4: {"name": "IDOR Notes API", "dir": "web-exploitation-challenges-4-idor-notes-api", "port": 8103, "kind": "notes-api"},
    5: {"name": "Compartmentalized Vault", "dir": "web-exploitation-challenges-5-compartmentalized-vault", "port": 8104, "kind": "vault-api"},
}


def run_command(cmd, description=""):
    print(f"  ► {description}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            print(f"    ✗ Failed: {error_msg}")
            return False
        return True
    except Exception as exc:
        print(f"    ✗ Error: {exc}")
        return False


class StaticDirectoryHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)


def start_static_server(challenge_dir: Path, port: int):
    handler = lambda *args, **kwargs: StaticDirectoryHandler(*args, directory=str(challenge_dir), **kwargs)
    server = ThreadingHTTPServer(("0.0.0.0", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def json_response(handler, status_code: int, payload: dict):
    data = json.dumps(payload).encode("utf-8")
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def file_response(handler, file_path: Path, content_type: str):
    data = file_path.read_bytes()
    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


NOTES = {
    101: {"owner": "alice", "title": "Shopping", "body": "Milk, eggs, bread"},
    102: {"owner": "alice", "title": "Reminder", "body": "Pay internet bill"},
    201: {"owner": "bob", "title": "Todo", "body": "Finish sprint report"},
    202: {"owner": "bob", "title": "Draft", "body": "Team offsite ideas"},
    9001: {"owner": "admin", "title": "Admin Secret", "body": "srcq{check_object_level_authorization}"},
}


COMPARTMENTS = {
    "public/alpha": {"label": "Alpha", "purpose": "customer dispatch", "records": {11: {"title": "Route Sheet", "body": "Dock 3 loads at 08:00"}, 12: {"title": "Label Codes", "body": "Blue crates continue north"}}},
    "public/beta": {"label": "Beta", "purpose": "inventory tracking", "records": {21: {"title": "Stock Count", "body": "Copper coils: 18"}, 22: {"title": "Short List", "body": "Replace broken seals"}}},
    "ops/delta": {"label": "Delta", "purpose": "operations review", "records": {31: {"title": "Shift Note", "body": "Rotate the perimeter cameras"}, 32: {"title": "Vendor Call", "body": "Confirm pickup window"}}},
    "vault": {"label": "Vault", "purpose": "restricted archive", "records": {9001: {"title": "Vault Record", "body": "srcq{normalize_before_authorizing}"}}},
}
VISIBLE_COMPARTMENTS = ["public/alpha", "public/beta", "ops/delta"]


def normalize_compartment(compartment: str) -> str:
    normalized = os.path.normpath(compartment).replace("\\", "/")
    if normalized in (".", ""):
        return ""
    return normalized.lstrip("./")


def start_api_server(challenge_dir: Path, port: int, kind: str):
    class ChallengeHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(challenge_dir), **kwargs)

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path

            if kind == "notes-api":
                if path in ("/", "/index.html"):
                    return file_response(self, challenge_dir / "index.html", "text/html; charset=utf-8")
                if path == "/style.css":
                    return file_response(self, challenge_dir / "style.css", "text/css; charset=utf-8")
                if path == "/script.js":
                    return file_response(self, challenge_dir / "script.js", "application/javascript; charset=utf-8")
                if path.startswith("/api/notes/"):
                    try:
                        note_id = int(path.rsplit("/", 1)[-1])
                    except ValueError:
                        return json_response(self, 400, {"error": "invalid note id"})

                    note = NOTES.get(note_id)
                    if not note:
                        return json_response(self, 404, {"error": "note not found"})

                    return json_response(self, 200, {"id": note_id, "owner": note["owner"], "title": note["title"], "body": note["body"]})

            if kind == "vault-api":
                if path in ("/", "/index.html"):
                    return file_response(self, challenge_dir / "index.html", "text/html; charset=utf-8")
                if path == "/style.css":
                    return file_response(self, challenge_dir / "style.css", "text/css; charset=utf-8")
                if path == "/script.js":
                    return file_response(self, challenge_dir / "script.js", "application/javascript; charset=utf-8")
                if path == "/api/compartments":
                    compartments = []
                    for compartment_name in VISIBLE_COMPARTMENTS:
                        compartment = COMPARTMENTS[compartment_name]
                        compartments.append({"path": compartment_name, "label": compartment["label"], "purpose": compartment["purpose"], "recordCount": len(compartment["records"])})

                    return json_response(self, 200, {"user": "mira", "role": "courier", "compartments": compartments})

                if path == "/api/records":
                    query = urllib.parse.parse_qs(parsed.query)
                    compartment = query.get("compartment", [""])[0]
                    record_id_text = query.get("id", [""])[0]

                    if not compartment or not record_id_text:
                        return json_response(self, 400, {"error": "missing compartment or id"})

                    try:
                        record_id = int(record_id_text)
                    except ValueError:
                        return json_response(self, 400, {"error": "invalid id"})

                    if not compartment.startswith(("public/", "ops/")):
                        return json_response(self, 403, {"error": "access denied"})

                    normalized = normalize_compartment(compartment)
                    compartment_data = COMPARTMENTS.get(normalized)
                    if not compartment_data:
                        return json_response(self, 404, {"error": "unknown compartment"})

                    record = compartment_data["records"].get(record_id)
                    if not record:
                        return json_response(self, 404, {"error": "record not found"})

                    return json_response(self, 200, {"compartment": normalized, "id": record_id, "title": record["title"], "body": record["body"]})

            return super().do_GET()

    server = ThreadingHTTPServer(("0.0.0.0", port), ChallengeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def start_challenge(challenge_num, config):
    challenge_dir = BASE_DIR / config["dir"]
    port = config["port"]
    kind = config["kind"]

    if not challenge_dir.exists():
        print(f"  ✗ Directory not found: {challenge_dir}")
        return None

    if kind == "static":
        server, _thread = start_static_server(challenge_dir, port)
        label = f"Challenge {challenge_num} (Static, port {port})"
    else:
        server, _thread = start_api_server(challenge_dir, port, kind)
        label = f"Challenge {challenge_num} ({kind.replace('-', ' ').title()}, port {port})"

    PROCESSES.append((challenge_num, server, label, port))
    print(f"  ✓ {label} started")
    return server


def print_summary():
    print("\n" + "=" * 70)
    print("✓ All challenges are running!")
    print("=" * 70)
    print("\n📋 Access your challenges at:\n")

    for challenge_num, config in CHALLENGES.items():
        print(f"  Challenge {challenge_num}: {config['name']:<35} http://localhost:{config['port']}")

    print("\n" + "=" * 70)
    print("Press Ctrl+C to stop all challenges")
    print("=" * 70 + "\n")


def cleanup():
    print("\n\n🛑 Shutting down all challenges...\n")
    for challenge_num, server, label, port in PROCESSES:
        try:
            server.shutdown()
            server.server_close()
            print(f"  ✓ Stopped {label}")
        except Exception as exc:
            print(f"  ✗ Error stopping {label}: {exc}")


def main():
    print("\n" + "=" * 70)
    print("  CTF Web Challenges: Master Setup & Launch")
    print("=" * 70)

    try:
        print("\n📦 Checking challenge directories...")
        for challenge_num, config in CHALLENGES.items():
            challenge_dir = BASE_DIR / config["dir"]
            if not challenge_dir.exists():
                print(f"✗ Missing directory for Challenge {challenge_num}: {challenge_dir}")
                return False

        print("\n🚀 Starting all challenges...\n")
        for challenge_num, config in CHALLENGES.items():
            print(f"  Starting Challenge {challenge_num}: {config['name']}")
            if start_challenge(challenge_num, config) is None:
                print(f"    ✗ Failed to start Challenge {challenge_num}")
                return False
            time.sleep(0.2)

        print_summary()

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        cleanup()
        print("✓ All challenges stopped\n")
        return True
    except Exception as exc:
        print(f"\n✗ Unexpected error: {exc}")
        cleanup()
        return False


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
