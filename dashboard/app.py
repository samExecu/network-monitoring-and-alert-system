"""
Flask web server + SocketIO for the real-time dashboard.

REST endpoints:
- GET / → serves index.html
- GET /api/stats → 24h uptime % and avg RTT per host
- GET /api/current → latest status per host (for status cards)
- GET /api/metrics → last 300 poll results
- GET /api/alerts → last 50 alerts
- GET /api/attacks → last 50 attack events
- GET /api/history/<host_ip> → RTT history for one host (for charts)

SocketIO events:
- Server → Client "update" - emitted every 10s, tells client to refresh
"""

import threading
import time
import logging
import config
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from database import database

logger = logging.getLogger("dashboard")

# Flask App Setup
app = Flask(__name__, template_folder="templates")
app.config["SECRET_KEY"] = "netmon-dashboard-secret"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

@app.route("/")
def index():
    # Serve the main dashboard page.
    return render_template("index.html")


@app.route("/api/stats")
def api_stats():
    #24-hour aggregated stats per host.
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
    #Live status of each host.
    return jsonify(database.get_current_status())


@app.route("/api/metrics")
def api_metrics():
    # Return the last 300 poll results.
    return jsonify(database.get_recent_metrics(300))


@app.route("/api/alerts")
def api_alerts():
    # Return the last 50 alerts.
    return jsonify(database.get_recent_alerts(50))


@app.route("/api/attacks")
def api_attacks():
    # Return the last 50 attack events.
    return jsonify(database.get_attack_events(50))


@app.route("/api/history/<path:host>")
def api_history(host):
    # RTT time series for one host, The host IP is passed in the URL, e.g. /api/history/8.8.8.8
    return jsonify(database.get_rtt_history(host, limit=60))


# ── Background SocketIO Push ──────────────────────────────────────────────────
def _push_loop():
    # Emit an 'update' event every 10 seconds so the dashboard auto-refreshes.
    while True:
        time.sleep(10)
        try:
            socketio.emit("update", {"ts": time.time()})
        except Exception as e:
            logger.error(f"SocketIO push error: {e}")


def start_push_thread():
    # Start the background thread for periodic SocketIO updates.
    t = threading.Thread(target=_push_loop, daemon=True)
    t.start()
