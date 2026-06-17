"""
Flask web server + SocketIO for the real-time dashboard.
Production-ready build with clean route configurations.
"""

import os
import threading
import time
import logging
from flask import Flask, render_template, jsonify, send_from_directory
from flask_socketio import SocketIO
from database import database

logger = logging.getLogger("dashboard")

# Find the absolute path to your 'dashboard/' folder
DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))

# Configure Flask
app = Flask(
    __name__,
    template_folder=os.path.join(DASHBOARD_DIR, "templates"),
    static_folder=os.path.join(DASHBOARD_DIR, "templates", "static"),
    static_url_path="/static"
)
app.config["SECRET_KEY"] = "netmon-dashboard-secret"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")


# Auto-Initialize Database
try:
    database.init_db()
except Exception as e:
    logger.debug(f"Database auto-init notice: {e}")


# Web UI Routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/fonts/<path:filename>")
def serve_fonts(filename):
    fonts_path = os.path.join(DASHBOARD_DIR, "templates", "fonts")
    return send_from_directory(fonts_path, filename)


# REST API Endpoints
@app.route("/api/stats")
def api_stats():
    # 24-hour aggregated stats per host.
    rows = database.get_host_stats()
    result = []
    for r in rows:
        total = r["total"] or 1
        up_count = r["up_count"] or 0
        result.append({
            "label": r["label"],
            "host": r["host"],
            "uptime": round((up_count / total) * 100, 1),
            "avg_rtt": r["avg_rtt"],
            "max_rtt": r["max_rtt"],
            "avg_http": r["avg_http_ms"],
            "last_seen": r["last_seen"],
        })
    return jsonify(result)


@app.route("/api/current")
def api_current():
    return jsonify(database.get_current_status())


@app.route("/api/metrics")
def api_metrics():
    return jsonify(database.get_recent_metrics(300))


@app.route("/api/alerts")
def api_alerts():
    return jsonify(database.get_recent_alerts(50))


@app.route("/api/attacks")
def api_attacks():
    return jsonify(database.get_attack_events(50))


@app.route("/api/history/<path:host>")
def api_history(host):
    return jsonify(database.get_rtt_history(host, limit=60))


# Background SocketIO Push
def _push_loop():
    while True:
        time.sleep(10)
        try:
            socketio.emit("update", {"ts": time.time()})
        except Exception as e:
            logger.error(f"SocketIO push error: {e}")

def start_push_thread():
    t = threading.Thread(target=_push_loop, daemon=True)
    t.start()
