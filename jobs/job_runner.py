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


def run_forever(interval_seconds=60):
    """
    Continuously run pending automation jobs.

    The runner checks for scheduled automation jobs,
    executes all jobs that are due, then waits for the
    configured interval before checking again.

    Args:
        interval_seconds (int):
            Number of seconds between job checks.
    """

    app = create_app()

    with app.app_context():

        app.logger.info(
            "Automation job runner started."
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

            time.sleep(interval_seconds)


if __name__ == "__main__":
    """
    Start the automation job runner.

    Default behavior:
    - Check pending jobs every 60 seconds.
    - Keep running until the process is stopped.
    """

    run_forever(interval_seconds=60)
