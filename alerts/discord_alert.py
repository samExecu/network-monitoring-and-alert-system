"""
Sends embed notifications to a Discord channel via webhook.

Setup:
1. Create a Discord server (free)
2. Go to a text channel > Edit Channel > Integrations > Webhooks
3. Create a new webhook and copy the URL
4. Paste it as DISCORD_WEBHOOK in your .env file
"""

import requests
import config
from datetime import datetime

# Embed colors
_COLORS = {
    "CRITICAL": 15548997,  # red
    "WARNING": 16705372,   # orange
    "INFO": 3447003,       # blue
    "RECOVERY": 5763719,   # green
}

# Severity labels
_LABELS = {
    "CRITICAL": "CRITICAL",
    "WARNING": "WARNING",
    "INFO": "INFO",
    "RECOVERY": "RECOVERY",
    "ATTACK": "ATTACK",
}


def send_discord_alert(label: str, host: str, alert_type: str,
                        message: str, severity: str = "WARNING") -> None:

    # Send an embed message to the configured Discord webhook, if not configured it'll end silently
    if not config.DISCORD_WEBHOOK:
        return

    severity_text = _LABELS.get(severity, "WARNING")
    color = _COLORS.get(severity, 16705372)

    payload = {
        "embeds": [{
            "title": f"{alert_type}: {label}",
            "description": message,
            "color": color,
            "fields": [
                {"name": "Host", "value": f"`{host}`", "inline": True},
                {"name": "Severity", "value": f"**{severity_text}**", "inline": True},
                {"name": "Time", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": False},
            ],
            "footer": {"text": "NetMon — Network Monitoring & Alert System"},
        }]
    }

    try:
        r = requests.post(config.DISCORD_WEBHOOK, json=payload, timeout=5)
        if r.status_code not in (200, 204):
            print(f"[DISCORD] Error {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"[DISCORD ERROR] {e}")


def send_attack_alert(host: str, attack_type: str, description: str) -> None:
    """Send a special red-alert embed for detected attacks."""
    if not config.DISCORD_WEBHOOK:
        return

    payload = {
        "embeds": [{
            "title": f"ATTACK DETECTED: {attack_type}",
            "description": description,
            "color": 15548997,
            "fields": [
                {"name": "Target Host", "value": f"`{host}`", "inline": True},
                {"name": "Time", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": True},
            ],
            "footer": {"text": "NetMon Security Alert"},
        }]
    }

    try:
        requests.post(config.DISCORD_WEBHOOK, json=payload, timeout=5)
    except Exception as e:
        print(f"[DISCORD ATTACK ALERT ERROR] {e}")


"""
Test Block
"""
if __name__ == "__main__":
    print("[TEST] Sending sample Discord alerts...")

    send_discord_alert(
        label="Localhost",
        host="127.0.0.1",
        alert_type="DOWN",
        message="Host unreachable",
        severity="CRITICAL"
    )

    send_attack_alert(
        host="127.0.0.1",
        attack_type="PORTSCAN",
        description="Detected port scan attempt"
    )

    print("[TEST] Done. Check your Discord channel for messages.")