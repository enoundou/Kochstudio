# services/automation_service.py

from datetime import datetime, UTC, timedelta

from models import db, AutomationJob, Reservation
from services.email_service import EmailService
from services.reservation_service import ReservationService


class AutomationService:
    """
    Service responsible for executing scheduled automation jobs.

    This service is typically called by a background worker,
    cron job, or scheduler.
    """

    @staticmethod
    def get_pending_jobs():
        """
        Retrieve all scheduled jobs that are ready to run.

        Returns:
            list[AutomationJob]:
                Scheduled automation jobs whose execution time
                is now or in the past.
        """

        return AutomationJob.query.filter(
            AutomationJob.status_code == "scheduled",
            AutomationJob.scheduled_at <= datetime.now(UTC)
        ).order_by(
            AutomationJob.scheduled_at.asc()
        ).all()

    @staticmethod
    def run_pending_jobs():
        """
        Execute all pending automation jobs.

        Returns:
            int:
                Number of processed jobs.
        """

        jobs = AutomationService.get_pending_jobs()

        for job in jobs:
            AutomationService.execute_job(job)

        return len(jobs)

    @staticmethod
    def execute_job(job):
        """
        Execute a single automation job.

        The method marks the job as running, dispatches it to
        the correct handler, and finally updates the job status.

        Args:
            job (AutomationJob): Automation job instance.

        Returns:
            AutomationJob:
                Updated automation job.
        """

        try:
            job.status_code = "running"
            job.attempts = (job.attempts or 0) + 1
            db.session.commit()

            if job.job_type_code == "send_conditions_after_30_min":
                AutomationService.send_conditions_email(job)

            elif job.job_type_code == "remind_conditions_after_2_days":
                AutomationService.send_conditions_reminder(job)

            elif job.job_type_code == "send_offer_catalogue":
                AutomationService.send_offer_catalogue(job)

            elif job.job_type_code == "remind_offer_after_2_days":
                AutomationService.send_offer_reminder(job)

            elif job.job_type_code == "confirm_reservation":
                AutomationService.confirm_reservation(job)

            elif job.job_type_code == "notify_manager_invoice":
                AutomationService.notify_manager_invoice(job)

            elif job.job_type_code == "send_calendar_invites":
                AutomationService.send_calendar_invites(job)

            else:
                raise ValueError(
                    f"Unknown automation job type: {job.job_type_code}"
                )

            job.status_code = "completed"
            job.executed_at = datetime.now(UTC)
            db.session.commit()

            return job

        except Exception as exc:
            job.status_code = "failed"
            job.last_error = str(exc)
            db.session.commit()

            return job

    @staticmethod
    def send_conditions_email(job):
        """
        Send reservation conditions to the customer.

        This job is executed 30 minutes after the initial
        reservation has been created.

        Args:
            job (AutomationJob): Automation job instance.
        """

        reservation = Reservation.query.get(job.reservation_id)

        if not reservation:
            raise ValueError("Reservation not found.")

        EmailService.send_conditions_email(reservation)

        reservation.status_code = "waiting_conditions_confirmation"
        reservation.current_step_code = "waiting_conditions_confirmation"
        reservation.updated_at = datetime.now(UTC)

        reminder_job = AutomationJob(
            reservation_id=reservation.id,
            job_type_code="remind_conditions_after_2_days",
            scheduled_at=datetime.now(UTC) + timedelta(days=2),
            status_code="scheduled"
        )

        db.session.add(reminder_job)
        db.session.commit()

    @staticmethod
    def send_conditions_reminder(job):
        """
        Send a reminder if conditions were not accepted yet.

        If the reservation is still waiting for condition
        confirmation, a reminder email is sent to the customer.

        Args:
            job (AutomationJob): Automation job instance.
        """

        reservation = Reservation.query.get(job.reservation_id)

        if not reservation:
            raise ValueError("Reservation not found.")

        if reservation.status_code != "waiting_conditions_confirmation":
            return

        EmailService.send_conditions_reminder(reservation)

    @staticmethod
    def send_offer_catalogue(job):
        """
        Send offer catalogue email to the customer.

        This job is executed after the customer has accepted
        the reservation conditions.

        Args:
            job (AutomationJob): Automation job instance.
        """

        reservation = Reservation.query.get(job.reservation_id)

        if not reservation:
            raise ValueError("Reservation not found.")

        EmailService.send_offer_catalogue(reservation)

        reservation.status_code = "waiting_offer_selection"
        reservation.current_step_code = "waiting_offer_selection"
        reservation.updated_at = datetime.now(UTC)

        reminder_job = AutomationJob(
            reservation_id=reservation.id,
            job_type_code="remind_offer_after_2_days",
            scheduled_at=datetime.now(UTC) + timedelta(days=2),
            status_code="scheduled"
        )

        db.session.add(reminder_job)
        db.session.commit()

    @staticmethod
    def send_offer_reminder(job):
        """
        Send a reminder if no offer has been selected yet.

        Args:
            job (AutomationJob): Automation job instance.
        """

        reservation = Reservation.query.get(job.reservation_id)

        if not reservation:
            raise ValueError("Reservation not found.")

        if reservation.status_code != "waiting_offer_selection":
            return

        EmailService.send_offer_reminder(reservation)

    @staticmethod
    def confirm_reservation(job):
        """
        Finalize the reservation.

        Args:
            job (AutomationJob): Automation job instance.
        """

        ReservationService.confirm_reservation(job.reservation_id)

    @staticmethod
    def notify_manager_invoice(job):
        """
        Notify the manager to create an invoice.

        Args:
            job (AutomationJob): Automation job instance.
        """

        reservation = Reservation.query.get(job.reservation_id)

        if not reservation:
            raise ValueError("Reservation not found.")

        EmailService.send_manager_invoice_request(reservation)

    @staticmethod
    def send_calendar_invites(job):
        """
        Send calendar invitations to collaborators.

        Args:
            job (AutomationJob): Automation job instance.
        """

        reservation = Reservation.query.get(job.reservation_id)

        if not reservation:
            raise ValueError("Reservation not found.")

        EmailService.send_calendar_invitations(reservation)