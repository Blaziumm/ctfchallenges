from __future__ import annotations

from .challenges_bp import bp
from CTFd.plugins import register_plugin_assets_directory, register_admin_plugin_menu_bar


def load(app):
    """CTFd plugin entrypoint called as load(app).

    Registers the challenge blueprint so routes like /challenge-4/ work
    inside a running CTFd instance without extra services.
    """
    register_plugin_assets_directory(app, base_path="/plugins/ctfchallenges/")
    app.register_blueprint(bp)
    register_admin_plugin_menu_bar("CTF Challenges", "/admin/plugins/ctfchallenges")
