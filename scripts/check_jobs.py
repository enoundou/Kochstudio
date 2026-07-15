from app import create_app
from models.models import AutomationJob, EmailLog, Reservation


def print_jobs():
    """
    Print recent automation jobs with their status and errors.
    """

    jobs = AutomationJob.query.order_by(
        AutomationJob.created_at.desc()
    ).limit(30).all()

    print("\nAutomation jobs")
    print("-" * 80)

    for job in jobs:
        print(
            f"id={job.id} "
            f"reservation={job.reservation_id} "
            f"type={job.job_type_code} "
            f"status={job.status_code} "
            f"scheduled_at={job.scheduled_at} "
            f"attempts={job.attempts} "
            f"error={job.last_error or ''}"
        )


def print_emails():
    """
    Print recent email logs with their status.
    """

    emails = EmailLog.query.order_by(
        EmailLog.created_at.desc()
    ).limit(30).all()

    print("\nEmail logs")
    print("-" * 80)

    for email in emails:
        print(
            f"id={email.id} "
            f"reservation={email.reservation_id} "
            f"type={email.email_type_code} "
            f"to={email.to_email} "
            f"status={email.status_code} "
            f"sent_at={email.sent_at} "
            f"subject={email.subject or ''}"
        )


def print_reservations():
    """
    Print recent reservations and workflow status.
    """

    reservations = Reservation.query.order_by(
        Reservation.created_at.desc()
    ).limit(15).all()

    print("\nReservations")
    print("-" * 80)

    for reservation in reservations:
        print(
            f"id={reservation.id} "
            f"number={reservation.reservation_number} "
            f"status={reservation.status_code} "
            f"step={reservation.current_step_code} "
            f"created_at={reservation.created_at}"
        )


if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        print_jobs()
        print_emails()
        print_reservations()