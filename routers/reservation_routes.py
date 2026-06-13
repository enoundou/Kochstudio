from flask import Blueprint, request, jsonify

from services.reservation_service import ReservationService


reservation_bp = Blueprint(
    "reservations",
    __name__,
    url_prefix="/api/reservations"
)


@reservation_bp.route("", methods=["POST"])
def create_reservation():
    """
    Create a new reservation.

    Expected payload:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+49123456789",
        "event_type_code": "company_event",
        "cooking_course_id": 1,
        "participant_count": 12,
        "first_choice_date": "2026-06-01",
        "first_choice_time": "18:00:00",
        "second_choice_date": "2026-06-02",
        "second_choice_time": "19:00:00",
        "note": "Vegetarian menu preferred"
    }

    Returns:
        JSON response containing the created reservation.
    """

    data = request.get_json()

    reservation = ReservationService.create_reservation(
        data
    )

    return jsonify({
        "success": True,
        "reservation_id": reservation.id,
        "reservation_number": reservation.reservation_number
    }), 201


@reservation_bp.route("/<int:reservation_id>", methods=["GET"])
def get_reservation(reservation_id):
    """
    Retrieve a reservation by its identifier.

    Args:
        reservation_id (int): Reservation identifier.

    Returns:
        JSON representation of the reservation.
    """

    reservation = ReservationService.get_reservation(
        reservation_id
    )

    if not reservation:
        return jsonify({
            "success": False,
            "message": "Reservation not found."
        }), 404

    return jsonify({
        "id": reservation.id,
        "reservation_number": reservation.reservation_number,
        "status_code": reservation.status_code,
        "event_type_code": reservation.event_type_code
    })


@reservation_bp.route("", methods=["GET"])
def get_reservations():
    """
    Retrieve all reservations.

    Returns:
        List of reservations ordered by creation date.
    """

    reservations = ReservationService.get_all_reservations()

    return jsonify([
        {
            "id": reservation.id,
            "reservation_number": reservation.reservation_number,
            "status_code": reservation.status_code
        }
        for reservation in reservations
    ])


@reservation_bp.route(
    "/<int:reservation_id>/confirm",
    methods=["POST"]
)
def confirm_reservation(reservation_id):
    """
    Confirm a reservation.

    Updates the reservation status to confirmed.

    Args:
        reservation_id (int): Reservation identifier.

    Returns:
        JSON confirmation response.
    """

    reservation = ReservationService.confirm_reservation(
        reservation_id
    )

    if not reservation:
        return jsonify({
            "success": False,
            "message": "Reservation not found."
        }), 404

    return jsonify({
        "success": True,
        "status_code": reservation.status_code
    })


@reservation_bp.route(
    "/<int:reservation_id>/cancel",
    methods=["POST"]
)
def cancel_reservation(reservation_id):
    """
    Cancel a reservation.

    Updates the reservation status to cancel.

    Args:
        reservation_id (int): Reservation identifier.

    Returns:
        JSON cancellation response.
    """

    reservation = ReservationService.cancel_reservation(
        reservation_id
    )

    if not reservation:
        return jsonify({
            "success": False,
            "message": "Reservation not found."
        }), 404

    return jsonify({
        "success": True,
        "status_code": reservation.status_code
    })


@reservation_bp.route("/<int:reservation_id>/billing-address", methods=["PUT"])
def update_billing_address(reservation_id):
    """
    Update the billing address of a reservation.

    Expected payload:
    {
        "billing_company_name": "ABC GmbH",
        "billing_first_name": "John",
        "billing_last_name": "Doe",
        "billing_street": "Main Street",
        "billing_house_number": "10",
        "billing_postal_code": "12345",
        "billing_city": "Berlin",
        "billing_country": "Germany"
    }

    Args:
        reservation_id (int): Reservation identifier.

    Returns:
        JSON response with updated reservation.
    """

    data = request.get_json()

    reservation = ReservationService.update_billing_address(
        reservation_id,
        data
    )

    if not reservation:
        return jsonify({
            "success": False,
            "message": "Reservation not found."
        }), 404

    return jsonify({
        "success": True,
        "reservation_id": reservation.id
    })


@reservation_bp.route("/conditions/<token>/accept", methods=["POST"])
def accept_conditions(token):
    """
    Accept reservation conditions.

    Triggered when the customer accepts the
    reservation conditions through the email link.

    Args:
        token (str): Confirmation token.

    Returns:
        JSON response.
    """

    reservation = ReservationService.accept_conditions(
        token
    )

    if not reservation:
        return jsonify({
            "success": False,
            "message": "Invalid token."
        }), 404

    return jsonify({
        "success": True,
        "status_code": reservation.status_code
    })


@reservation_bp.route(
    "/conditions/<token>/reject",
    methods=["POST"]
)
def reject_conditions(token):
    """
    Reject reservation conditions.

    Triggered when the customer rejects the
    reservation conditions through the email link.

    Args:
        token (str): Confirmation token.

    Returns:
        JSON response.
    """

    reservation = ReservationService.reject_conditions(
        token
    )

    if not reservation:
        return jsonify({
            "success": False,
            "message": "Invalid token."
        }), 404

    return jsonify({
        "success": True,
        "status_code": reservation.status_code
    })


@reservation_bp.route(
    "/<int:reservation_id>/offer",
    methods=["POST"]
)
def select_offer(reservation_id):
    """
    Select an offer catalogue for a reservation.

    Expected payload:
    {
        "catalogue_id": 3,
        "note": "Preferred menu option"
    }

    Args:
        reservation_id (int): Reservation identifier.

    Returns:
        JSON response with created offer selection.
    """

    data = request.get_json()

    selection = ReservationService.select_offer(
        reservation_id=reservation_id,
        catalogue_id=data["catalogue_id"],
        note=data.get("note")
    )

    if not selection:
        return jsonify({
            "success": False,
            "message": "Reservation not found."
        }), 404

    return jsonify({
        "success": True,
        "selection_id": selection.id
    })

