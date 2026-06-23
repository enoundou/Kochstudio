from flask import Blueprint, request, jsonify

from services.reservation_service import ReservationService

reservation_bp = Blueprint(
    "reservations",
    __name__,
    url_prefix="/api/reservations"
)


def serialize_reservation(reservation):
    """
    Convert a reservation model instance into a JSON dictionary.

    Args:
        reservation (Reservation): Reservation instance.

    Returns:
        dict:
            Serialized reservation data.
    """

    return {
        "id": reservation.id,
        "reservation_number": reservation.reservation_number,
        "customer_id": reservation.customer_id,
        "customer_name": (
            reservation.customer.name
            if reservation.customer
            else None
        ),
        "customer_email": (
            reservation.customer.email
            if reservation.customer
            else None
        ),
        "event_type_code": reservation.event_type_code,
        "cooking_course_id": reservation.cooking_course_id,
        "participant_count": reservation.participant_count,
        "first_choice_date": (
            reservation.first_choice_date.isoformat()
            if reservation.first_choice_date
            else None
        ),
        "first_choice_time": (
            reservation.first_choice_time.isoformat()
            if reservation.first_choice_time
            else None
        ),
        "second_choice_date": (
            reservation.second_choice_date.isoformat()
            if reservation.second_choice_date
            else None
        ),
        "second_choice_time": (
            reservation.second_choice_time.isoformat()
            if reservation.second_choice_time
            else None
        ),
        "note": reservation.note,
        "billing_company_name": reservation.billing_company_name,
        "billing_first_name": reservation.billing_first_name,
        "billing_last_name": reservation.billing_last_name,
        "billing_street": reservation.billing_street,
        "billing_house_number": reservation.billing_house_number,
        "billing_address_line_2": reservation.billing_address_line_2,
        "billing_postal_code": reservation.billing_postal_code,
        "billing_city": reservation.billing_city,
        "billing_state_region": reservation.billing_state_region,
        "billing_country": reservation.billing_country,
        "status_code": reservation.status_code,
        "current_step_code": reservation.current_step_code,
        "created_at": (
            reservation.created_at.isoformat()
            if reservation.created_at
            else None
        ),
        "updated_at": (
            reservation.updated_at.isoformat()
            if reservation.updated_at
            else None
        ),
        "confirmed_at": (
            reservation.confirmed_at.isoformat()
            if reservation.confirmed_at
            else None
        ),
        "cancelled_at": (
            reservation.cancelled_at.isoformat()
            if reservation.cancelled_at
            else None
        )
    }


def validate_required_fields(data, required_fields):
    """
    Validate that all required fields exist in the request payload.

    Args:
        data (dict): Request JSON payload.
        required_fields (list[str]): Required field names.

    Returns:
        str | None:
            Missing field name if validation fails,
            otherwise None.
    """

    for field in required_fields:
        if not data.get(field):
            return field

    return None


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

    data = request.get_json() or {}

    missing_field = validate_required_fields(
        data,
        [
            "name",
            "email",
            "event_type_code"
        ]
    )

    if missing_field:
        return jsonify({
            "success": False,
            "message": f"{missing_field} is required."
        }), 400

    try:
        reservation = ReservationService.create_reservation(
            data
        )

        return jsonify({
            "success": True,
            "reservation": serialize_reservation(
                reservation
            )
        }), 201

    except Exception as exc:
        return jsonify({
            "success": False,
            "message": str(exc)
        }), 500


@reservation_bp.route("", methods=["GET"])
def get_reservations():
    """
    Retrieve all reservations.

    Returns:
        JSON list of reservations ordered by creation date.
    """

    reservations = ReservationService.get_all_reservations()

    return jsonify([
        serialize_reservation(reservation)
        for reservation in reservations
    ])


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

    return jsonify(

        serialize_reservation(reservation)
    )


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
        "reservation": serialize_reservation(
            reservation
        )
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
        "reservation": serialize_reservation(
            reservation
        )
    })


@reservation_bp.route(
    "/<int:reservation_id>/billing-address",
    methods=["PUT"]
)
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

    data = request.get_json() or {}

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
        "reservation": serialize_reservation(
            reservation
        )
    })


@reservation_bp.route(
    "/conditions/<token>/accept",
    methods=["POST"]
)
def accept_conditions(token):
    """
    Accept reservation conditions.

    Triggered when the customer accepts the reservation
    conditions through the email link.

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
        "reservation": serialize_reservation(
            reservation
        )
    })


@reservation_bp.route(
    "/conditions/<token>/reject",
    methods=["POST"]
)
def reject_conditions(token):
    """
    Reject reservation conditions.

    Triggered when the customer rejects the reservation
    conditions through the email link.

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
        "reservation": serialize_reservation(
            reservation
        )
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

    data = request.get_json() or {}

    if not data.get("catalogue_id"):
        return jsonify({
            "success": False,
            "message": "catalogue_id is required."
        }), 400

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
        "selection_id": selection.id,
        "reservation_id": selection.reservation_id,
        "catalogue_id": selection.catalogue_id
    })
