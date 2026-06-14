"""
Real-time anomaly and attack detection engine.
Detections:
  1. HOST_DOWN        → host stopped responding entirely
  2. HOST_FLAPPING    → host going up/down repeatedly (unstable link or attack)
  3. LATENCY_SPIKE    → RTT jumped 4x above rolling average (flood/congestion)
  4. HIGH_PACKET_LOSS → more than 30% of recent pings failed
  5. HTTP_ERROR       → HTTP 4xx or 5xx response
  6. SLOW_HTTP        → HTTP response took more than 3 seconds
  7. PORT_OPENED      → new port appeared on a host (possible compromise)
  8. PORT_CLOSED      → previously open port is now closed

When an anomaly is found:
  1. Logged to the `alerts` table in SQLite
  2. Discord embed fired
  3. Email sent
  4. Cooldown applied, same alert won't fire again for 2 minutes
"""

import collections
import time
import logging
import config
from database import database
from alerts import discord_alert, email_alert

logger = logging.getLogger("anomaly")

class AnomalyDetector:
    def __init__(self):
        # Rolling RTT buffer per host: last 20 readings
        self.rtt_history = collections.defaultdict(lambda: collections.deque(maxlen=20))
        # Rolling up/down buffer per host: last 10 polls
        self.status_history = collections.defaultdict(lambda: collections.deque(maxlen=10))
        # Port state baseline per host: {port: was_open}
        self.port_baseline = {}
        # Last alert timestamps for cooldown throttling: {key: epoch}
        self.last_alert_ts = {}

    # Internal helpers
    def _cooldown_ok(self, key: str) -> bool:
        # Return True if enough time has passed to fire this alert again
        now = time.time()
        if now - self.last_alert_ts.get(key, 0) > config.ALERT_COOLDOWN_SECONDS:
            self.last_alert_ts[key] = now
            return True
        return False

    def _fire(self, host: str, label: str, alert_type: str,
              message: str, severity: str) -> None:
        # Log the alert and send notifications, with cooldown
        logger.warning(f"[{severity}] {label} | {alert_type}: {message}")
        database.log_alert(host, label, alert_type, message, severity)
        if self._cooldown_ok(f"{host}:{alert_type}"):
            discord_alert.send_discord_alert(label, host, alert_type, message, severity)
            email_alert.send_email_alert(label, host, alert_type, message, severity)

    def _fire_attack(self, host: str, attack_type: str,
                    description: str, severity: str = "CRITICAL") -> None:
        # Log and alert on detected attacks
        logger.warning(f"[ATTACK] {host} | {attack_type}: {description}")
        database.log_attack_event(host, attack_type, description, severity)
        if self._cooldown_ok(f"{host}:ATTACK:{attack_type}"):
            discord_alert.send_attack_alert(host, attack_type, description)

    # Detection methods, called by scheduler after each poll
    def check_availability(self, host: str, label: str, is_up: bool) -> None:
        """Detect host going down or flapping."""
        history = self.status_history[host]
        history.append(1 if is_up else 0)

        if not is_up:
            msg = f"{label} ({host}) is not responding."
            self._fire(host, label, "HOST_DOWN", msg, "CRITICAL")

        # Flapping = state changed 4+ times in last 10 polls
        if len(history) >= 6:
            changes = sum(1 for i in range(1, len(history)) if history[i] != history[i - 1])
            if changes >= 4:
                msg = (f"{label} is unstable — changed state {changes} times "
                      f"in the last {len(history)} checks. Possible attack or link issue.")
                self._fire(host, label, "HOST_FLAPPING", msg, "WARNING")
                self._fire_attack(host, "FLAPPING", msg, "WARNING")

    def check_latency(self, host: str, label: str, rtt_ms: float | None) -> None:
        # Detect latency spikes. This catches ICMP floods and DDoS-induced congestion.
        if rtt_ms is None:
            return  # host down, handled by check_availability

        history = self.rtt_history[host]
        history.append(rtt_ms)
        if len(history) < 5:
            return  # not enough data for a baseline yet

        prev = list(history)[:-1]
        avg_rtt = sum(prev) / len(prev)
        threshold = max(avg_rtt * config.LATENCY_SPIKE_FACTOR, config.LATENCY_THRESHOLD_MS)

        if avg_rtt > 0 and rtt_ms > threshold:
            severity = "CRITICAL" if rtt_ms > avg_rtt * 8 else "WARNING"
            msg = (f"RTT jumped to {rtt_ms:.0f}ms "
                  f"(rolling avg: {avg_rtt:.1f}ms, spike factor: {rtt_ms/avg_rtt:.1f}x). "
                  f"Possible flood or severe congestion.")
            self._fire(host, label, "LATENCY_SPIKE", msg, severity)
            if severity == "CRITICAL":
                self._fire_attack(host, "POSSIBLE_FLOOD",
                                  f"Latency spike of {rtt_ms:.0f}ms detected on {label}.",
                                  "CRITICAL")

    def check_packet_loss(self, host: str, label: str) -> None:
        # Detect high packet loss. If >30% of recent pings failed, something is wrong.
        history = self.status_history[host]
        if len(history) < 5:
            return

        loss_pct = (history.count(0) / len(history)) * 100
        if loss_pct >= config.PACKET_LOSS_THRESHOLD:
            severity = "CRITICAL" if loss_pct >= 60 else "WARNING"
            msg = (f"Packet loss at {loss_pct:.0f}% "
                  f"({history.count(0)} failures in last {len(history)} checks).")
            self._fire(host, label, "HIGH_PACKET_LOSS", msg, severity)

    def check_http(self, host: str, label: str,
                  status_code: int | None, response_ms: float | None) -> None:
        # Detect HTTP errors and slow responses.
        if status_code is None:
            return  # connection failure

        if status_code >= 500:
            msg = f"HTTP {status_code} server error — service may be down or broken."
            self._fire(host, label, "HTTP_SERVER_ERROR", msg, "CRITICAL")
        elif status_code >= 400:
            msg = f"HTTP {status_code} error on {host}."
            self._fire(host, label, "HTTP_CLIENT_ERROR", msg, "WARNING")

        if response_ms and response_ms > config.HTTP_SLOW_THRESHOLD_MS:
            msg = (f"HTTP response took {response_ms:.0f}ms — "
                  f"service appears slow (threshold: {config.HTTP_SLOW_THRESHOLD_MS}ms).")
            self._fire(host, label, "SLOW_HTTP", msg, "WARNING")

    def check_port_changes(self, host: str, label: str, port_results: dict) -> None:
        """
        Compare current port scan against the stored baseline.
        New open port → could be a backdoor or new service.
        Port now closed → service may have crashed or been blocked.
        """
        if host not in self.port_baseline:
            # First scan — store as baseline, don’t alert
            self.port_baseline[host] = {p: d["open"] for p, d in port_results.items()}
            logger.info(f"[{label}] Port baseline saved: "
                        f"{sum(1 for d in port_results.values() if d['open'])} ports open")
            return

        baseline = self.port_baseline[host]
        for port, data in port_results.items():
            was_open = baseline.get(port, False)
            is_open = data["open"]
            service = data["service"]

            if not was_open and is_open:
                msg = (f"Port {port} ({service}) is now OPEN on {host}. "
                      f"This is a new service — verify it is expected.")
                self._fire(host, label, "PORT_OPENED", msg, "WARNING")
                self._fire_attack(host, "NEW_PORT",
                                  f"Unexpected port {port} ({service}) opened on {label}.",
                                  "WARNING")
            elif was_open and not is_open:
                msg = f"Port {port} ({service}) is now CLOSED on {host}."
                self._fire(host, label, "PORT_CLOSED", msg, "INFO")
        # Update baseline with latest scan
        self.port_baseline[host] = {p: d["open"] for p, d in port_results.items()}

detector = AnomalyDetector()
