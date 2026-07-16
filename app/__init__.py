from flask import Flask
import yaml
import os


def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


_SEV_COLORS = {
    "critical": "danger",
    "high":     "warning",
    "medium":   "primary",
    "low":      "info",
    "info":     "secondary",
}


def _badge(severity: str) -> str:
    color = _SEV_COLORS.get(severity.lower(), "secondary")
    return f'<span class="badge bg-{color}">{severity.upper()}</span>'


def create_app():
    app = Flask(__name__)
    config = load_config()
    app.config["SIEM_CONFIG"] = config
    app.secret_key = "siem-dev-secret-key"

    app.jinja_env.filters["badge"] = _badge

    from app.database import init_db
    init_db(config["siem"]["database"])

    from app.routes import bp
    app.register_blueprint(bp)

    return app
