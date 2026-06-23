"""
Checks each target in config.TARGETS every POLL_INTERVAL_SECONDS.
Each target runs in its own thread so slow hosts don't block fast ones.
"""

import threading
import logging
import config
from monitor import ping_monitor, port_monitor, http_monitor
from database import database
from detection.anamoly import detector

logger = logging.getLogger("scheduler")


def _poll_one(target: dict) -> None:
    # Poll a single target, log results, and run anomaly checks
    host = target["host"]
    label = target["label"]
    mtype = target.get("type", "ping")

    rtt_ms = None
    http_code = None
    http_ms = None
    is_up = False

    # Ping check
    rtt_ms = ping_monitor.ping_host(host)
    is_up = rtt_ms is not None

    # HTTP check if type is http
    if mtype == "http" and "url" in target:
        http_code, http_ms = http_monitor.check_http(target["url"])
        if http_code and 200 <= http_code < 400:
            is_up = True

    # Log metrics to DB
    database.log_metric(host, label, rtt_ms, is_up, http_code, http_ms)

    # Run anomaly detectors
    detector.check_availability(host, label, is_up)
    detector.check_latency(host, label, rtt_ms)
    detector.check_packet_loss(host, label)
    if http_code is not None:
        detector.check_http(host, label, http_code, http_ms)

    #Note: only use port scan on networks you are allowed
    # port_results = port_monitor.scan_common_ports(host)
    # detector.check_port_changes(host, label, port_results)

    # # Log each port state to DB so dashboard can show them
    # for port, info in port_results.items():
    #     database.log_port_state(
    #         host=host,
    #         label=label,
    #         port=port,
    #         service=info["service"],
    #         is_open=info["open"]
    #     )

    # Console log
    if is_up:
        rtt_str = f"{rtt_ms:.0f}ms" if rtt_ms else "—"
        http_str = f" | HTTP {http_code} ({http_ms:.0f}ms)" if http_code else ""
        logger.info(f" UP {label:<22} RTT: {rtt_str}{http_str}")
    else:
        logger.warning(f" DOWN {label:<22} {host}")


def poll_all() -> None:
    # Poll all targets concurrently using threads.
    logger.info(f"Polling {len(config.TARGETS)} targets...")
    threads = [
        threading.Thread(target=_poll_one, args=(t,), daemon=True)
        for t in config.TARGETS
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=15)  # max 20s per poll cycle

