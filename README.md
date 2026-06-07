# NetMon - Network Monitoring & Alert System

> **On‑Going Project** — Actively being developed, features may change.

A real-time network health monitor with a live web dashboard, anomaly detection, and multi-channel alerts.
Built with Python. Works on Windows, macOS, and Linux.

---

## What it does

- **Monitors** any host or service — via ICMP ping, TCP port check, or HTTP/HTTPS
- **Detects anomalies** — latency spikes, packet loss, host flapping, port changes, slow HTTP
- **Alerts in real time** — Discord embed + HTML email when something breaks
- **Displays a live dashboard** — auto-updating charts, uptime %, alert feed, attack events
- **Flags attacks** — ICMP floods, Slowloris HTTP DoS, unexpected port openings

---

## Tech Stack

| Layer      | Technology                                                      |
| ---------- | --------------------------------------------------------------- |
| Monitor    | Python `subprocess` (cross-platform ping), `socket`, `requests` |
| Scheduling | APScheduler                                                     |
| Storage    | SQLite (`sqlite3` built-in)                                     |
| Alerts     | Discord Webhooks, Gmail SMTP                                    |
| Dashboard  | Flask + Flask-SocketIO + Chart.js                               |
| Detection  | Custom anomaly engine                                           |

---

## Project Status

This project is in **active development**.
Expect frequent updates, new features, and breaking changes until the first stable release.

---

# Team Members:

1. Bikram Timalsina
2. Karan Bhatt
3. Rojan Tamang
4. Sushant Ale Magar
