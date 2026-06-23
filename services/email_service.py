from datetime import datetime, UTC

from flask import current_app

from models import (
    db,
    EmailLog,
    Manager,
    Collaborator
)


class EmailService:
    """
    Service responsible for sending emails and
    storing email audit logs.

    All workflow decisions should be handled by
    AutomationService, not by EmailService.
    """

    @staticmethod
    def send_email(
            reservation,
            email_type_code,
            recipient_email,
            subject,
            body
    ):
        """
        Send an email and create an email log entry.

        Args:
            reservation (Reservation): Reservation instance.
            email_type_code (str): Email type identifier.
            recipient_email (str): Recipient email address.
            subject (str): Email subject.
            body (str): Email body content.

        Returns:
            EmailLog:
                Created email log entry.
        """

        try:
            #
            # TODO:
            # Integrate SMTP, SendGrid, Mailgun,
            # Microsoft Graph or other provider.
            #
            current_app.logger.info(
                f"Sending email to {recipient_email}"
            )

            email_log = EmailLog(
                reservation_id=reservation.id,
                email_type_code=email_type_code,
                to_email=recipient_email,
                subject=subject,
                body=body,
                sent_at=datetime.now(UTC),
                status_code="sent"
            )

            db.session.add(email_log)
            db.session.commit()

            return email_log

        except Exception as exc:

            email_log = EmailLog(
                reservation_id=reservation.id,
                email_type_code=email_type_code,
                to_email=recipient_email,
                subject=subject,
                body=body,
                status_code="failed"
            )

            db.session.add(email_log)
            db.session.commit()

            raise exc

    @staticmethod
    def send_conditions_email(reservation):
        """
        Send reservation conditions to the customer.

        Args:
            reservation (Reservation): Reservation instance.

        Returns:
            EmailLog
        """

        subject = (
            f"Reservation {reservation.reservation_number}"
        )

        body = (
            "Please review and confirm the reservation "
            "conditions using the provided link."
        )

        return EmailService.send_email(
            reservation=reservation,
            email_type_code="conditions_info",
            recipient_email=reservation.customer.email,
            subject=subject,
            body=body
        )

    @staticmethod
    def send_conditions_reminder(reservation):
        """
        Send a reminder to confirm reservation conditions.

        Args:
            reservation (Reservation): Reservation instance.

        Returns:
            EmailLog
        """

        subject = (
            f"Reminder - Reservation "
            f"{reservation.reservation_number}"
        )

        body = (
            "Please confirm the reservation conditions."
        )

        return EmailService.send_email(
            reservation=reservation,
            email_type_code="conditions_reminder",
            recipient_email=reservation.customer.email,
            subject=subject,
            body=body
        )

    @staticmethod
    def send_offer_catalogue(reservation):
        """
        Send available offer catalogues to the customer.

        Args:
            reservation (Reservation): Reservation instance.

        Returns:
            EmailLog
        """

        subject = "Available Offers"

        body = (
            "Please review the available offers and "
            "select your preferred catalogue."
        )

        return EmailService.send_email(
            reservation=reservation,
            email_type_code="offer_catalogue",
            recipient_email=reservation.customer.email,
            subject=subject,
            body=body
        )

    @staticmethod
    def send_offer_reminder(reservation):
        """
        Send a reminder to select an offer catalogue.

        Args:
            reservation (Reservation): Reservation instance.

        Returns:
            EmailLog
        """

        subject = (
            "Reminder - Offer Selection Required"
        )

        body = (
            "Please select your preferred offer catalogue."
        )

        return EmailService.send_email(
            reservation=reservation,
            email_type_code="offer_reminder",
            recipient_email=reservation.customer.email,
            subject=subject,
            body=body
        )

    @staticmethod
    def send_reservation_confirmation(reservation):
        """
        Send final reservation confirmation.

        Args:
            reservation (Reservation): Reservation instance.

        Returns:
            EmailLog
        """

        subject = (
            f"Reservation Confirmed "
            f"({reservation.reservation_number})"
        )

        body = (
            "Your reservation has been confirmed."
        )

        return EmailService.send_email(
            reservation=reservation,
            email_type_code="reservation_confirmed",
            recipient_email=reservation.customer.email,
            subject=subject,
            body=body
        )

    @staticmethod
    def send_manager_invoice_request(reservation):
        """
        Notify managers that an invoice should be created.

        Args:
            reservation (Reservation): Reservation instance.
        """

        managers = Manager.query.all()

        for manager in managers:
            EmailService.send_email(
                reservation=reservation,
                email_type_code="manager_invoice_request",
                recipient_email=manager.email,
                subject="Invoice Creation Required",
                body=(
                    f"Please create an invoice for "
                    f"reservation "
                    f"{reservation.reservation_number}."
                )
            )

    @staticmethod
    def send_calendar_invitations(reservation):
        """
        Send calendar invitations to collaborators.

        Args:
            reservation (Reservation): Reservation instance.
        """

        collaborators = Collaborator.query.all()

        for collaborator in collaborators:
            EmailService.send_email(
                reservation=reservation,
                email_type_code="collaborator_invitation",
                recipient_email=collaborator.email,
                subject="New Reservation Assignment",
                body=(
                    f"You have been assigned to "
                    f"reservation "
                    f"{reservation.reservation_number}."
                )
            )
