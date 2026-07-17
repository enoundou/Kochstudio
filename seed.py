"""
Database seed script.

Creates all required reference data for:

- Event types
- Reservation statuses
- Workflow steps
- Email types
- Email statuses
- Automation job types
- Job statuses
- Invitation statuses

Run:

    python seed.py
"""

from app import create_app
from models.models import (
    db,
    EventType,
    ReservationStatus,
    WorkflowStep,
    EmailType,
    EmailStatus,
    AutomationJobType,
    JobStatus,
    InvitationStatus
)


def seed_event_types():
    """
    Seed event types.
    """

    items = [
        EventType(
            code="company_event",
            name_de="Firmen Event",
            name_en="Company Event"
        ),
        EventType(
            code="cooking_experience",
            name_de="Koch Erlebnis",
            name_en="Cooking Experience"
        ),
        EventType(
            code="kids_event",
            name_de="Kinder Event",
            name_en="Kids Event"
        ),
        EventType(
            code="other",
            name_de="Sonstige",
            name_en="Other"
        )
    ]

    for item in items:
        if not EventType.query.get(item.code):
            db.session.add(item)


def seed_reservation_statuses():
    """
    Seed reservation statuses.
    """

    items = [
        ReservationStatus(
            code="temporary",
            name_de="Temporär",
            name_en="Temporary",
            sort_order=1
        ),
        ReservationStatus(
            code="waiting_conditions_confirmation",
            name_de="Warte auf Bedingungen",
            name_en="Waiting Conditions",
            sort_order=2
        ),
        ReservationStatus(
            code="conditions_confirmed",
            name_de="Bedingungen bestätigt",
            name_en="Conditions Confirmed",
            sort_order=3
        ),
        ReservationStatus(
            code="conditions_rejected",
            name_de="Bedingungen abgelehnt",
            name_en="Conditions Rejected",
            sort_order=4
        ),
        ReservationStatus(
            code="waiting_offer_selection",
            name_de="Warte auf Angebotswahl",
            name_en="Waiting Offer Selection",
            sort_order=5
        ),
        ReservationStatus(
            code="offer_selected",
            name_de="Angebot ausgewählt",
            name_en="Offer Selected",
            sort_order=6
        ),
        ReservationStatus(
            code="confirmed",
            name_de="Bestätigt",
            name_en="Confirmed",
            sort_order=7
        ),
        ReservationStatus(
            code="cancelled",
            name_de="Storniert",
            name_en="Cancelled",
            sort_order=8
        )
    ]

    for item in items:
        if not ReservationStatus.query.get(item.code):
            db.session.add(item)


def seed_workflow_steps():
    """
    Seed workflow steps.
    """

    items = [
        WorkflowStep(
            code="reservation_received",
            name_de="Reservierung erhalten",
            name_en="Reservation Received",
            sort_order=1
        ),
        WorkflowStep(
            code="waiting_conditions_confirmation",
            name_de="Bedingungen offen",
            name_en="Waiting Conditions",
            sort_order=2
        ),
        WorkflowStep(
            code="conditions_confirmed",
            name_de="Bedingungen bestätigt",
            name_en="Conditions Confirmed",
            sort_order=3
        ),
        WorkflowStep(
            code="waiting_offer_selection",
            name_de="Angebot auswählen",
            name_en="Waiting Offer Selection",
            sort_order=4
        ),
        WorkflowStep(
            code="offer_selected",
            name_de="Angebot gewählt",
            name_en="Offer Selected",
            sort_order=5
        ),
        WorkflowStep(
            code="confirmed",
            name_de="Bestätigt",
            name_en="Confirmed",
            sort_order=6
        )
    ]

    for item in items:
        if not WorkflowStep.query.get(item.code):
            db.session.add(item)


def seed_email_types():
    """
    Seed email types.
    """

    items = [
        ("conditions_info", "Bedingungen", "Conditions"),
        ("conditions_reminder", "Erinnerung Bedingungen", "Conditions Reminder"),
        ("offer_catalogue", "Angebote", "Offer Catalogue"),
        ("offer_reminder", "Erinnerung Angebot", "Offer Reminder"),
        ("reservation_confirmed", "Reservierung bestätigt", "Reservation Confirmed"),
        ("manager_invoice_request", "Rechnung erstellen", "Invoice Request"),
        ("collaborator_invitation", "Mitarbeiter Einladung", "Collaborator Invitation")
    ]

    for code, de, en in items:
        if not EmailType.query.get(code):
            db.session.add(
                EmailType(
                    code=code,
                    name_de=de,
                    name_en=en
                )
            )


def seed_email_statuses():
    """
    Seed email statuses.
    """

    items = [
        ("pending", "Ausstehend", "Pending"),
        ("sent", "Gesendet", "Sent"),
        ("failed", "Fehlgeschlagen", "Failed")
    ]

    for code, de, en in items:
        if not EmailStatus.query.get(code):
            db.session.add(
                EmailStatus(
                    code=code,
                    name_de=de,
                    name_en=en
                )
            )


def seed_job_types():
    """
    Seed automation job types.
    """

    items = [
        ("send_conditions_after", "Bedingungen senden", "Send Conditions"),
        ("remind_conditions_after", "Bedingungen erinnern", "Remind Conditions"),
        ("send_offer_catalogue", "Angebot senden", "Send Offer"),
        ("remind_offer_after", "Angebot erinnern", "Remind Offer"),
        ("confirm_reservation", "Reservierung bestätigen", "Confirm Reservation"),
        ("notify_manager_invoice", "Manager informieren", "Notify Manager"),
        ("send_calendar_invites", "Kalender Einladungen", "Calendar Invitations")
    ]

    for code, de, en in items:
        if not AutomationJobType.query.get(code):
            db.session.add(
                AutomationJobType(
                    code=code,
                    name_de=de,
                    name_en=en
                )
            )


def seed_job_statuses():
    """
    Seed automation job statuses.
    """

    items = [
        ("scheduled", "Geplant", "Scheduled"),
        ("running", "Läuft", "Running"),
        ("completed", "Abgeschlossen", "Completed"),
        ("failed", "Fehlgeschlagen", "Failed")
    ]

    for code, de, en in items:
        if not JobStatus.query.get(code):
            db.session.add(
                JobStatus(
                    code=code,
                    name_de=de,
                    name_en=en
                )
            )


def seed_invitation_statuses():
    """
    Seed invitation statuses.
    """

    items = [
        ("pending", "Ausstehend", "Pending"),
        ("sent", "Gesendet", "Sent"),
        ("accepted", "Angenommen", "Accepted"),
        ("declined", "Abgelehnt", "Declined")
    ]

    for code, de, en in items:
        if not InvitationStatus.query.get(code):
            db.session.add(
                InvitationStatus(
                    code=code,
                    name_de=de,
                    name_en=en
                )
            )


def run_seed():
    """
    Execute all seed operations.
    """

    seed_event_types()
    seed_reservation_statuses()
    seed_workflow_steps()
    seed_email_types()
    seed_email_statuses()
    seed_job_types()
    seed_job_statuses()
    seed_invitation_statuses()

    db.session.commit()

    print("Seed completed successfully.")


if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        run_seed()
