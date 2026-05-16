Integration notes — mounting challenges inside a CTFd Flask app
=============================================================

Goal
----
Provide a small Flask blueprint that serves the challenge static files and the two small API backends. This lets you mount the challenges inside the existing CTFd web app so no extra systemd/service units are required.

Files
-----
- `challenges_bp.py` — Flask `Blueprint` that serves `/challenge-1/`..`/challenge-5/` routes.

Quick install
-------------
1. Copy `challenges_bp.py` into your CTFd project (for example, into `ctfd/plugins/` or your app package).
2. In your CTFd app factory (where the Flask `app` is created), register the blueprint:

```python
from ctfd import create_app
from challenges_bp import bp as challenges_bp

app = create_app()
app.register_blueprint(challenges_bp)

# Now open: http://<ctfd-host>/challenge-4/ and http://<ctfd-host>/challenge-5/
```

Notes and tips
-------------
- The blueprint serves files from the challenge folders in this repository. If you copy only `challenges_bp.py` into CTFd, also copy the challenge folders (the `web-exploitation-challenges-*` directories) next to it so the static paths resolve correctly.
- The blueprint is intentionally minimal — it returns the same JSON data and route behaviour as the offline launcher. Mounting it avoids running separate Python services.
- If you prefer to keep the master launcher as a manually-run process (no systemd), run `python3 run_all_challenges.py` in a screen/tmux session and configure your reverse proxy to map a path to the local ports. Either approach avoids creating a systemd unit.

Reverse-proxy example (if you decide to run the launcher manually):

```nginx
location /challenge-4/ { proxy_pass http://127.0.0.1:8103/; }
location /challenge-5/ { proxy_pass http://127.0.0.1:8104/; }
```

Retained files
--------------

This minimal repository includes only the files needed for production hosting of the challenges when integrated into CTFd:

- `plugins/ctfchallenges/` — CTFd plugin that registers the challenge routes (`load(app)` entrypoint).
- `web-exploitation-challenges-*` — All challenge static folders and assets.
- `README.md` — This installation and usage notes.

To install the plugin into your production CTFd instance, copy the `plugins/ctfchallenges` folder into your CTFd `plugins` directory and restart CTFd.

