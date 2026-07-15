from datetime import datetime, UTC

from flask import current_app

from models.models import (
    db,
    CalendarInvitation,
    Collaborator
)


class CalendarService:
    """
    Service responsible for creating calendar invitations
    and storing invitation records.

    This service can later be connected to Google Calendar,
    Microsoft Outlook, or another calendar provider.
    """

    @staticmethod
    def create_calendar_event(reservation):
        """
        Create a calendar event for a confirmed reservation.

        Args:
            reservation (Reservation): Confirmed reservation instance.

        Returns:
            str:
                External calendar event identifier.
        """

        # TODO:
        # Replace this placeholder with a real calendar API integration.
        # Example providers:
        # - Google Calendar API
        # - Microsoft Graph Calendar API
        # - CalDAV
        calendar_event_id = (
            f"calendar-event-{reservation.reservation_number}"
        )

        current_app.logger.info(
            f"Calendar event created: {calendar_event_id}"
        )

        return calendar_event_id

    @staticmethod
    def create_invitations_for_collaborators(reservation):
        """
        Create calendar invitations for all active collaborators.

        Args:
            reservation (Reservation): Reservation instance.

        Returns:
            list[CalendarInvitation]:
                Created calendar invitation records.
        """

        collaborators = Collaborator.query.all()
        invitations = []

        calendar_event_id = CalendarService.create_calendar_event(
            reservation
        )

        for collaborator in collaborators:
            invitation = CalendarInvitation(
                reservation_id=reservation.id,
                invitee_email=collaborator.email,
                invitee_name=collaborator.name,
                calendar_event_id=calendar_event_id,
                sent_at=datetime.now(UTC),
                status_code="sent"
            )

            db.session.add(invitation)
            invitations.append(invitation)

        db.session.commit()

        return invitations

    @staticmethod
    def send_calendar_invitations(reservation):
        """
        Send calendar invitations to collaborators.

        This method currently creates invitation records and
        marks them as sent. Later, it can be extended to send
        real calendar invites through an external provider.

        Args:
            reservation (Reservation): Reservation instance.

        Returns:
            list[CalendarInvitation]:
                Created invitation records.
        """

        return CalendarService.create_invitations_for_collaborators(
            reservation
        )

    @staticmethod
    def update_invitation_status(invitation_id, status_code):
        """
        Update the status of a calendar invitation.

        Args:
            invitation_id (int): Calendar invitation identifier.
            status_code (str): New invitation status.

        Returns:
            CalendarInvitation | None:
                Updated invitation or None if not found.
        """

        invitation = CalendarInvitation.query.get(invitation_id)

        if not invitation:
            return None

        invitation.status_code = status_code

        if status_code in ["accepted", "declined"]:
            invitation.responded_at = datetime.now(UTC)

        db.session.commit()

        return invitation
