# services/automation_service.py

from datetime import datetime, UTC, timedelta

from flask import current_app
from sqlalchemy import func, or_
from models.models import db, AutomationJob, Reservation
from models.models import ReservationCondition
from services.calendar_service import CalendarService
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
        Retrieve scheduled or retryable failed jobs that are ready to run.

        Failed jobs are retried while attempts is below 3. NULL attempts and
        NULL scheduled_at values are handled explicitly for older rows.
        """

        now = datetime.now(UTC)

        return AutomationJob.query.filter(
            AutomationJob.status_code.in_([
                "scheduled",
                "failed"
            ]),
            or_(
                AutomationJob.scheduled_at.is_(None),
                AutomationJob.scheduled_at <= now
            ),
            func.coalesce(AutomationJob.attempts, 0) < 3
        ).order_by(
            AutomationJob.scheduled_at.asc(),
            AutomationJob.id.asc()
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

        Reminder jobs are completed after the reminder handler returns without
        an exception. If a reminder is no longer needed, the job is also
        completed and the reason is stored in last_error for the dashboard.
        """

        try:
            job.status_code = "running"
            job.attempts = (job.attempts or 0) + 1
            job.last_error = None
            db.session.commit()

            handler_result = None

            if job.job_type_code == "send_conditions_after":
                handler_result = AutomationService.send_conditions_email(job)

            elif job.job_type_code == "remind_conditions_after":
                handler_result = AutomationService.send_conditions_reminder(job)

            elif job.job_type_code == "send_offer_catalogue":
                handler_result = AutomationService.send_offer_catalogue(job)

            elif job.job_type_code == "remind_offer_after":
                handler_result = AutomationService.send_offer_reminder(job)

            elif job.job_type_code == "confirm_reservation":
                handler_result = AutomationService.confirm_reservation(job)

            elif job.job_type_code == "notify_manager_invoice":
                handler_result = AutomationService.notify_manager_invoice(job)

            elif job.job_type_code == "send_calendar_invites":
                handler_result = AutomationService.send_calendar_invites(job)

            else:
                raise ValueError(
                    f"Unknown automation job type: {job.job_type_code}"
                )

            job.status_code = "completed"
            job.executed_at = datetime.now(UTC)

            if handler_result is False:
                job.last_error = "Reminder skipped because it is no longer needed."

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

        This job only sends the conditions email and updates the reservation
        status. It does not create an automatic reminder job.
        """

        reservation = Reservation.query.get(job.reservation_id)

        if not reservation:
            raise ValueError("Reservation not found.")

        EmailService.send_conditions_email(reservation)

        condition = ReservationCondition.query.filter_by(
            reservation_id=reservation.id
        ).first()

        if condition:
            condition.sent_at = datetime.now(UTC)

        reservation.status_code = "waiting_conditions_confirmation"
        reservation.current_step_code = "waiting_conditions_confirmation"
        reservation.updated_at = datetime.now(UTC)

        db.session.commit()


    @staticmethod
    def send_conditions_reminder(job):
        """
        Send a reminder if conditions were not accepted yet.

        Returns:
            bool: True when the reminder email was sent, False when it was no
            longer needed.
        """

        reservation = Reservation.query.get(job.reservation_id)

        if not reservation:
            raise ValueError("Reservation not found.")

        if reservation.status_code != "waiting_conditions_confirmation":
            return False

        EmailService.send_conditions_reminder(reservation)

        return True

    @staticmethod
    def send_offer_catalogue(job):
        """
        Send offer catalogue email to the customer.

        The shared reservation service prevents duplicate offer emails and
        schedules the offer reminder only when needed.
        """

        reservation = Reservation.query.get(job.reservation_id)

        if not reservation:
            raise ValueError("Reservation not found.")

        ReservationService.send_offer_catalogue_now(reservation)


    @staticmethod
    def send_offer_reminder(job):
        """
        Send a reminder if no offer has been selected yet.

        Returns:
            bool: True when the reminder email was sent, False when it was no
            longer needed.
        """

        reservation = Reservation.query.get(job.reservation_id)

        if not reservation:
            raise ValueError("Reservation not found.")

        if reservation.status_code != "waiting_offer_selection":
            return False

        EmailService.send_offer_reminder(reservation)

        return True

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

        CalendarService.send_calendar_invitations(reservation)
        EmailService.send_calendar_invitations(reservation)
