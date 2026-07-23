from flask import Blueprint, render_template, request

from models.models import ReservationCondition
from services.email_service import EmailService
from services.reservation_service import ReservationService


customer_workflow_bp = Blueprint(
    "customer_workflow",
    __name__
)


@customer_workflow_bp.route("/conditions/<token>/accept", methods=["GET"])
def accept_conditions_page(token):
    """
    Accept reservation conditions from an email link.
    """

    try:
        reservation = ReservationService.accept_conditions(token)
    except Exception:
        return render_template(
            "message.html",
            title="Bedingungen bestütigt",
            message=(
                "Vielen Dank. Ihre Bestätigung wurde gespeichert. "
                "Die Angebotsmail konnte gerade nicht automatisch gesendet werden; "
                "wir melden uns kurzfristig bei Ihnen."
            )
        ), 500

    if not reservation:
        return render_template(
            "message.html",
            title="Link ungültig",
            message="Der Bestätigungslink ist ungültig oder nicht mehr verfügbar."
        ), 404

    return render_template(
        "message.html",
        title="Bedingungen bestätigt",
        message="Vielen Dank. Die Angebotsauswahl wurde Ihnen per E-Mail gesendet."
    )


@customer_workflow_bp.route("/conditions/<token>/reject", methods=["GET"])
def reject_conditions_page(token):
    """
    Reject reservation conditions from an email link.
    """

    reservation = ReservationService.reject_conditions(token)

    if not reservation:
        return render_template(
            "message.html",
            title="Link ungültig",
            message="Der Ablehnungslink ist ungültig oder nicht mehr verfügbar."
        ), 404

    return render_template(
        "message.html",
        title="Buchung storniert",
        message="Die Bedingungen wurden abgelehnt. Ihre Buchung wurde storniert."
    )


@customer_workflow_bp.route("/offer-selection/<token>", methods=["GET"])
def offer_selection_page(token: object) -> tuple[str, int] | str:
    """
    Render the customer offer selection form.
    """

    condition = ReservationCondition.query.filter_by(
        confirmation_token=token
    ).first()

    if not condition:
        return render_template(
            "message.html",
            title="Link ungültig",
            message="Der Angebotslink ist ungültig oder nicht mehr verfügbar."
        ), 404

    offers = EmailService.get_offer_price_categories(condition.reservation)
    offer_options = [
        {
            "id": offer.id,
            "label": EmailService.build_offer_category_line(offer).lstrip("- ")
        }
        for offer in offers
    ]

    return render_template(
        "offer_selection.html",
        reservation=condition.reservation,
        offer_options=offer_options,
        token=token
    )


@customer_workflow_bp.route("/offer-selection/<token>", methods=["POST"])
def submit_offer_selection(token):
    """
    Store the selected offer and invoice address from a standard HTML form post.
    """

    condition = ReservationCondition.query.filter_by(
        confirmation_token=token
    ).first()

    if not condition:
        return render_template(
            "message.html",
            title="Link ungültig",
            message="Der Angebotslink ist ungültig oder nicht mehr verfügbar."
        ), 404

    form_data = request.form.to_dict()

    selection = ReservationService.select_offer(
        reservation_id=condition.reservation_id,
        course_price_category_id=form_data.get("course_price_category_id"),
        note=form_data.get("note"),
        billing_data=form_data
    )

    if not selection:
        return render_template(
            "message.html",
            title="Fehler",
            message="Die Angebotsauswahl konnte nicht gespeichert werden."
        ), 400

    return render_template(
        "message.html",
        title="Angebot gewählt",
        message="Vielen Dank. Der Termin wird nun endgültig reserviert und das Team wird informiert."
    )
