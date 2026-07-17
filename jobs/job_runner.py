import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from models.models import AutomationJob, db
from services.automation_service import AutomationService


def log(message):
    """
    Print a timestamped runner message immediately.
    """

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def run_once(app):
    """
    Run all pending automation jobs once.
    """

    with app.app_context():
        pending_jobs = AutomationService.get_pending_jobs()

        if pending_jobs:
            job_summary = ", ".join(
                f"#{job.id}:{job.job_type_code}:{job.status_code}:attempts={job.attempts or 0}"
                for job in pending_jobs
            )
            log(f"Found {len(pending_jobs)} pending job(s): {job_summary}")
        else:
            log("Found 0 pending job(s).")

        processed_count = AutomationService.run_pending_jobs()
        db.session.remove()

    log(f"Processed {processed_count} automation job(s).")
    return processed_count


def run_forever(interval_minutes=None):
    """
    Continuously run pending automation jobs.
    """

    app = create_app()

    if interval_minutes is None:
        interval_minutes = app.config.get(
            "JOB_RUNNER_INTERVAL",
            2
        )

    log("Automation job runner started.")
    log(f"Project root: {PROJECT_ROOT}")
    log(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    log(f"Interval: {interval_minutes} minute(s)")

    while True:
        try:
            run_once(app)
        except KeyboardInterrupt:
            log("Automation job runner stopped.")
            break
        except Exception as exc:
            log(f"Automation job runner failed: {exc}")
            with app.app_context():
                db.session.rollback()
                db.session.remove()

        time.sleep(interval_minutes * 60)


def main():
    """
    Start the job runner from the command line.
    """

    parser = argparse.ArgumentParser(
        description="Run KochStudio automation jobs."
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run pending jobs once and stop."
    )
    parser.add_argument(
        "--interval-minutes",
        type=float,
        default=None,
        help="Override JOB_RUNNER_INTERVAL from .env."
    )

    args = parser.parse_args()

    if args.once:
        app = create_app()
        log("Running automation jobs once.")
        log(f"Project root: {PROJECT_ROOT}")
        log(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        run_once(app)
        return

    run_forever(
        interval_minutes=args.interval_minutes
    )


if __name__ == "__main__":
    main()