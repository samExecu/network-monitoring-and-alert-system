"""
Entry point. Run this to start everything.
Dashboard is accessible at: http://localhost:5000
Works on Windows, macOS, and Linux.
"""
import sys
import os
import logging
import platform

os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join("logs", "monitor.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("main")


def start_monitoring():
    """Initialize DB, run first poll immediately, then schedule every N seconds."""
    from apscheduler.schedulers.background import BackgroundScheduler
    from database import database
    from scheduler import poll_all
    import config

    database.init_db()
    logger.info(f"Platform   : {platform.system()} {platform.release()}")
    logger.info(f"Python     : {sys.version.split()[0]}")
    logger.info(f"Targets    : {len(config.TARGETS)} hosts")
    logger.info(f"Poll every : {config.POLL_INTERVAL_SECONDS}s")
    logger.info(f"Dashboard  : http://localhost:{config.DASHBOARD_PORT}")
    logger.info("─" * 55)

    # First poll right now so dashboard has data immediately
    poll_all()

    sched = BackgroundScheduler(daemon=True, timezone="UTC")
    sched.add_job(
        poll_all,
        "interval",
        seconds=config.POLL_INTERVAL_SECONDS,
        id="poll_all",
        max_instances=1
    )
    sched.start()
    return sched


if __name__ == "__main__":
    from dashboard.app import app, socketio, start_push_thread
    import config

    sched = start_monitoring()
    start_push_thread()

    try:
        # use_reloader=False is required when running APScheduler in the same process
        socketio.run(
            app,
            host=config.DASHBOARD_HOST,
            port=config.DASHBOARD_PORT,
            debug=False,
            use_reloader=False,
            log_output=False,
        )
    except KeyboardInterrupt:
        logger.info("Shutting down. Goodbye.")
        sched.shutdown(wait=False)
