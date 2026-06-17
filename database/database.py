"""
Handles all SQLite operations.
We have kept SQL queries in separate .sql files under /sql directory.
"""

import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'monitor.db')
SQL_DIR = os.path.join(os.path.dirname(__file__), '..', 'sql')


def _connect():
    # Make sure that the data folder exists and return a connection.
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_conn():
    # Context manager so we don't forget to close the connections.
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


def _load_sql(filename):
    # Loader to load SQL code from the /sql directory.
    path = os.path.join(SQL_DIR, filename)
    with open(path, 'r') as f:
        return f.read()


def init_db():
    # Creates the tables if they don’t exist.
    with db_conn() as conn:
        c = conn.cursor()
        c.execute(_load_sql("create-metrics.sql"))
        c.execute(_load_sql("create-alerts.sql"))
        c.execute(_load_sql("create-attack-events.sql"))
        conn.commit()
    print("Database Initialized.")

# Writing data into the database
def log_metric(host, label, rtt_ms, is_up, http_code=None, http_ms=None):
    # Record one monitoring datapoint (ping/HTTP).
    with db_conn() as conn:
        conn.execute(_load_sql("insert-metric.sql"), (
            host, label, rtt_ms, 1 if is_up else 0,
            http_code, http_ms, datetime.now().isoformat()
        ))
        conn.commit()


def log_alert(host, label, alert_type, message, severity):
    # Record an alert event, could be like the host being down.
    with db_conn() as conn:
        conn.execute(_load_sql("insert-alert.sql"), (
            host, label, alert_type, message,
            severity, datetime.now().isoformat()
        ))
        conn.commit()


def log_attack_event(host, attack_type, description, severity):
    # Record a flagged attack/anomaly event.
    with db_conn() as conn:
        conn.execute(_load_sql("insert-attack-event.sql"), (
            host, attack_type, description,
            severity, datetime.now().isoformat()
        ))
        conn.commit()


# Reading from the database
def get_host_stats():
    # Getting the 24h uptime % and average RTT per host.
    with db_conn() as conn:
        rows = conn.execute(_load_sql("get-host-status.sql")).fetchall()
    return [dict(r) for r in rows]


def get_recent_metrics(limit=300):
    # Get the most recent monitoring datapoints.
    with db_conn() as conn:
        rows = conn.execute(_load_sql("get-recent-metrics.sql"), (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_rtt_history(host, limit=60):
    # Get the RTT readings for one host for the charts.
    with db_conn() as conn:
        rows = conn.execute(_load_sql("get-rtt-history.sql"), (host, limit)).fetchall()
    return [dict(r) for r in reversed(rows)]


def get_recent_alerts(limit=50):
    # Get the latest alert events.
    with db_conn() as conn:
        rows = conn.execute(_load_sql("get-recent-alerts.sql"), (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_attack_events(limit=50):
    # Get the latest attack/anomaly events.
    with db_conn() as conn:
        rows = conn.execute(_load_sql("get-attack-events.sql"), (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_current_status():
    # Get latest status per host for dashboard cards.
    with db_conn() as conn:
        rows = conn.execute(_load_sql("get-current-status.sql")).fetchall()
    return [dict(r) for r in rows]


"""
Test Block

if __name__ == "__main__":
    print("[TEST] Initializing database...")
    init_db()

    # Insert some dummy data
    log_metric("127.0.0.1", "Localhost", 12.5, True, http_code=200, http_ms=45.2)
    log_alert("127.0.0.1", "Localhost", "DOWN", "Host unreachable", "CRITICAL")
    log_attack_event("127.0.0.1", "PORTSCAN", "Detected port scan attempt", "WARNING")

    # Get and display the results
    print("[TEST] Recent metrics:", get_recent_metrics(limit=3))
    print("[TEST] Recent alerts:", get_recent_alerts(limit=3))
    print("[TEST] Attack events:", get_attack_events(limit=3))
    print("[TEST] Current status:", get_current_status())
"""
