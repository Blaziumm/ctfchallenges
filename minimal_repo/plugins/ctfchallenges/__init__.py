from __future__ import annotations

from .challenges_bp import bp


def load(app):
    """CTFd plugin entrypoint called as load(app).

    Registers the challenge blueprint so routes like /challenge-4/ work
    inside a running CTFd instance without extra services.
    """
    app.register_blueprint(bp)
