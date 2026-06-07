"""
config.py — All settings live here.
To add a new host: add a dict to TARGETS.
type "ping" = just ping it (RTT + up/down)
type "http" = ping + HTTP check (add "url" key)
type "port" = ping + specific port check
"""
import os
from dotenv import load_dotenv
load_dotenv()
# Hosts to monitor

TARGETS = [
# Common Internet Hosts
  {
    "host": "8.8.8.8",
    "label": "Google DNS",
    "type": "ping",
  },
  {
    "host": "1.1.1.1",
    "label": "Cloudflare DNS",
    "type": "ping",
  },
  {
    "host": "google.com",
    "label": "Google HTTPS",
    "type": "http",
    "url": "https://www.google.com",
  },
  {
    "host": "github.com",
    "label": "GitHub",
    "type": "http",
    "url": "https://github.com",
  },

  # Home Router IP
  {
    "host": "192.168.1.1",
    "label": "Home Router",
    "type": "ping",
  },
]

# Alert thresholds
LATENCY_THRESHOLD_MS = 150 # ms - alert if RTT exceeds this
PACKET_LOSS_THRESHOLD = 30 # % - alert if packet loss exceeds this
HTTP_SLOW_THRESHOLD_MS = 3000 # ms - alert if HTTP response takes this long
LATENCY_SPIKE_FACTOR = 4 # x - alert if RTT is 4x the rolling average

# Polling
POLL_INTERVAL_SECONDS = 30 # how often to check all targets

# Alert cooldown
ALERT_COOLDOWN_SECONDS = 120

# Loaded from .env
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK", "")
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT", "")

# Dashboard
DASHBOARD_HOST = "0.0.0.0"
DASHBOARD_PORT = 5000
