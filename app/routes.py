from flask import Blueprint, render_template, request, jsonify, current_app
from app.database import get_events, get_alerts, get_stats

bp = Blueprint("main", __name__)


@bp.route("/")
def dashboard():
    stats = get_stats()
    config = current_app.config["SIEM_CONFIG"]
    return render_template("dashboard.html", stats=stats, config=config)


@bp.route("/events")
def events():
    severity = request.args.get("severity")
    source = request.args.get("source")
    page = max(1, int(request.args.get("page", 1)))
    limit = 50
    offset = (page - 1) * limit
    rows = get_events(limit=limit, offset=offset, severity=severity, source=source)
    config = current_app.config["SIEM_CONFIG"]
    return render_template(
        "events.html",
        events=rows,
        page=page,
        severity=severity or "",
        source=source or "",
        config=config,
    )


@bp.route("/alerts")
def alerts():
    page = max(1, int(request.args.get("page", 1)))
    limit = 50
    offset = (page - 1) * limit
    rows = get_alerts(limit=limit, offset=offset)
    config = current_app.config["SIEM_CONFIG"]
    return render_template("alerts.html", alerts=rows, page=page, config=config)


# --- JSON API endpoints (for live dashboard refresh) ---

@bp.route("/api/stats")
def api_stats():
    return jsonify(get_stats())


@bp.route("/api/events")
def api_events():
    severity = request.args.get("severity")
    source = request.args.get("source")
    limit = min(int(request.args.get("limit", 50)), 500)
    offset = int(request.args.get("offset", 0))
    return jsonify(get_events(limit=limit, offset=offset, severity=severity, source=source))


@bp.route("/api/alerts")
def api_alerts():
    limit = min(int(request.args.get("limit", 50)), 500)
    offset = int(request.args.get("offset", 0))
    return jsonify(get_alerts(limit=limit, offset=offset))
