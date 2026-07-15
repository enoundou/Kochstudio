import time

from app import create_app
from services.automation_service import AutomationService


def run_once():
    """
    Run pending automation jobs once.

    This function is useful for:
    - Manual execution
    - Testing
    - Cron jobs
    - Scheduled server tasks

    Returns:
        int:
            Number of processed automation jobs.
    """

    app = create_app()

    with app.app_context():
        processed_count = AutomationService.run_pending_jobs()

        app.logger.info(
            f"Processed {processed_count} automation job(s)."
        )

        return processed_count


def run_forever(interval_minutes=None):
    """
    Continuously run pending automation jobs.

    The runner checks for scheduled automation jobs,
    executes all jobs that are due, then waits for the
    configured interval before checking again.

    Args:
        interval_minutes (int):
            Number of minutes between job checks.
    """

    app = create_app()

    with app.app_context():

        if interval_minutes is None:
            interval_minutes = app.config.get(
                "JOB_RUNNER_INTERVAL",
                1
            )

        app.logger.info(
            f"Automation job runner started. Interval: {interval_minutes} minute(s)."
        )

        while True:
            try:
                processed_count = (
                    AutomationService.run_pending_jobs()
                )

                app.logger.info(
                    f"Processed {processed_count} automation job(s)."
                )

            except Exception as exc:
                app.logger.exception(
                    f"Automation job runner failed: {exc}"
                )

            time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    """
    Start the automation job runner.

    Default behavior:
    - Check pending jobs using JOB_RUNNER_INTERVAL from .env.
    - Keep running until the process is stopped.
    """

    run_forever()
