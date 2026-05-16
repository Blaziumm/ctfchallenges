from __future__ import annotations

from pathlib import Path
from flask import Blueprint, current_app, jsonify, request, send_from_directory, abort

BASE_DIR = Path(__file__).parent.parent.resolve()

bp = Blueprint("ctf_challenges", __name__)

CHALLENGES = {
    1: {"dir": "web-exploitation-challenges-1-hidden-admin-panel", "kind": "static"},
    2: {"dir": "web-exploitation-challenges-2-sql-injection-login", "kind": "static"},
    3: {"dir": "web-exploitation-challenges-3-xss-discovery", "kind": "static"},
    4: {"dir": "web-exploitation-challenges-4-idor-notes-api", "kind": "notes-api"},
    5: {"dir": "web-exploitation-challenges-5-compartmentalized-vault", "kind": "vault-api"},
}

# Data used by the API challenges (copied from the offline launcher)
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


def _challenge_dir(challenge_num: int) -> Path:
    conf = CHALLENGES.get(challenge_num)
    if not conf:
        raise KeyError("unknown challenge")
    return BASE_DIR / conf["dir"]


def _send_static(challenge_num: int, filename: str):
    d = _challenge_dir(challenge_num)
    fp = d / filename
    if not fp.exists():
        abort(404)
    return send_from_directory(str(d), filename)


# Static challenge routes (serve index and static assets)
@bp.route("/challenge-<int:cid>/")
@bp.route("/challenge-<int:cid>/index.html")
def challenge_index(cid: int):
    return _send_static(cid, "index.html")


@bp.route("/challenge-<int:cid>/<path:filename>")
def challenge_static(cid: int, filename: str):
    return _send_static(cid, filename)


# API challenge: notes (challenge 4)
@bp.route("/challenge-4/api/notes/<int:note_id>")
def api_notes_get(note_id: int):
    note = NOTES.get(note_id)
    if not note:
        return jsonify({"error": "note not found"}), 404
    return jsonify({"id": note_id, "owner": note["owner"], "title": note["title"], "body": note["body"]})


# API challenge: vault (challenge 5)
@bp.route("/challenge-5/api/compartments")
def api_compartments():
    compartments = []
    for name in VISIBLE_COMPARTMENTS:
        c = COMPARTMENTS[name]
        compartments.append({"path": name, "label": c["label"], "purpose": c["purpose"], "recordCount": len(c["records"])})
    return jsonify({"user": "mira", "role": "courier", "compartments": compartments})


@bp.route("/challenge-5/api/records")
def api_records():
    compartment = request.args.get("compartment", "")
    record_id_text = request.args.get("id", "")
    if not compartment or not record_id_text:
        return jsonify({"error": "missing compartment or id"}), 400
    try:
        record_id = int(record_id_text)
    except ValueError:
        return jsonify({"error": "invalid id"}), 400

    if not compartment.startswith(("public/", "ops/")):
        return jsonify({"error": "access denied"}), 403

    normalized = Path(compartment).as_posix().lstrip("./")
    compartment_data = COMPARTMENTS.get(normalized)
    if not compartment_data:
        return jsonify({"error": "unknown compartment"}), 404

    record = compartment_data["records"].get(record_id)
    if not record:
        return jsonify({"error": "record not found"}), 404

    return jsonify({"compartment": normalized, "id": record_id, "title": record["title"], "body": record["body"]})
