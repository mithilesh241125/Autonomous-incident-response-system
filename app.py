from __future__ import annotations

import atexit
from datetime import datetime
from typing import Dict

from flask import Flask, jsonify, render_template

from analyzer import LogAnalyzer
from config import settings
from monitor import MonitoringService
from storage import SQLiteStorage


app = Flask(__name__)
repository = SQLiteStorage(settings.database_path)
monitor = MonitoringService(repository, settings)
monitor.start()
atexit.register(monitor.stop)
atexit.register(repository.close)


def create_default_health() -> Dict[str, object]:
    """Return the default health payload before the first monitoring cycle."""
    return {
        "api_status": "Unknown",
        "cpu_usage": 0,
        "simulated_anomaly": False,
        "status": "STARTING",
        "checked_at": "Not checked yet",
    }


def build_dashboard_data() -> Dict[str, object]:
    """Assemble a template-friendly snapshot from SQLite and the log file."""
    analyzer = LogAnalyzer(settings.log_file)
    health = repository.get_latest_health() or create_default_health()
    incidents = repository.list_incidents(settings.dashboard_limit)
    actions = repository.list_actions(settings.dashboard_limit)
    alerts = repository.list_alerts(settings.dashboard_limit)
    analysis = repository.list_log_analysis(settings.dashboard_limit)
    logs = analyzer.read_logs()[-settings.dashboard_limit:]

    stats = {
        "total": len(incidents),
        "high": sum(1 for incident in incidents if incident.get("severity") == "HIGH"),
        "open": sum(1 for incident in incidents if incident.get("status") == "OPEN"),
        "resolved": sum(1 for incident in incidents if incident.get("status") == "RESOLVED"),
    }

    active_incidents = [incident for incident in incidents if incident.get("status") != "RESOLVED"]
    resolved_incidents = [incident for incident in incidents if incident.get("status") == "RESOLVED"]
    latest_action = actions[0] if actions else None
    latest_alert = alerts[0] if alerts else None
    last_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "health": health,
        "incidents": incidents,
        "active_incidents": active_incidents,
        "resolved_incidents": resolved_incidents,
        "actions": actions,
        "alerts": alerts,
        "analysis": analysis,
        "logs": logs,
        "stats": stats,
        "latest_action": latest_action,
        "latest_alert": latest_alert,
        "last_refresh": last_refresh,
    }


@app.route("/")
def dashboard():
    """Render the main incident response dashboard."""
    return render_template("dashboard.html", data=build_dashboard_data())


@app.route("/api/status")
def api_status():
    """Return the latest data as JSON for debugging or future frontends."""
    return jsonify(build_dashboard_data())


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
