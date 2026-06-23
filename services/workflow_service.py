# services/workflow_service.py

from datetime import datetime, UTC

from models import db, Reservation


class WorkflowService:
    """
    Service responsible for validating and applying reservation
    workflow state transitions.

    This service centralizes workflow rules so that routes,
    automation jobs, and other services do not update workflow
    states directly without validation.
    """

    ALLOWED_TRANSITIONS = {
        "temporary": [
            "waiting_conditions_confirmation",
            "cancelled"
        ],
        "waiting_conditions_confirmation": [
            "conditions_confirmed",
            "conditions_rejected",
            "cancelled"
        ],
        "conditions_confirmed": [
            "waiting_offer_selection",
            "cancelled"
        ],
        "waiting_offer_selection": [
            "offer_selected",
            "cancelled"
        ],
        "offer_selected": [
            "confirmed",
            "cancelled"
        ],
        "confirmed": [],
        "cancelled": []
    }

    @staticmethod
    def can_transition(current_status, new_status):
        """
        Check whether a reservation status transition is allowed.

        Args:
            current_status (str): Current reservation status code.
            new_status (str): Target reservation status code.

        Returns:
            bool:
                True if the transition is allowed, otherwise False.
        """

        allowed_statuses = WorkflowService.ALLOWED_TRANSITIONS.get(
            current_status,
            []
        )

        return new_status in allowed_statuses

    @staticmethod
    def update_status(reservation_id, new_status):
        """
        Update the reservation status if the transition is valid.

        Args:
            reservation_id (int): Reservation identifier.
            new_status (str): Target reservation status code.

        Returns:
            Reservation | None:
                Updated reservation instance, or None if the
                reservation does not exist.

        Raises:
            ValueError:
                If the requested status transition is not allowed.
        """

        reservation = Reservation.query.get(reservation_id)

        if not reservation:
            return None

        current_status = reservation.status_code

        if not WorkflowService.can_transition(
                current_status,
                new_status
        ):
            raise ValueError(
                f"Invalid workflow transition: "
                f"{current_status} -> {new_status}"
            )

        reservation.status_code = new_status
        reservation.current_step_code = new_status
        reservation.updated_at = datetime.now(UTC)

        if new_status == "confirmed":
            reservation.confirmed_at = datetime.now(UTC)

        if new_status == "cancelled":
            reservation.cancelled_at = datetime.now(UTC)

        db.session.commit()

        return reservation

    @staticmethod
    def mark_waiting_for_conditions(reservation_id):
        """
        Move a reservation to the conditions confirmation step.

        Args:
            reservation_id (int): Reservation identifier.

        Returns:
            Reservation | None
        """

        return WorkflowService.update_status(
            reservation_id,
            "waiting_conditions_confirmation"
        )

    @staticmethod
    def mark_conditions_confirmed(reservation_id):
        """
        Mark reservation conditions as confirmed.

        Args:
            reservation_id (int): Reservation identifier.

        Returns:
            Reservation | None
        """

        return WorkflowService.update_status(
            reservation_id,
            "conditions_confirmed"
        )

    @staticmethod
    def mark_conditions_rejected(reservation_id):
        """
        Mark reservation conditions as rejected.

        Args:
            reservation_id (int): Reservation identifier.

        Returns:
            Reservation | None
        """

        return WorkflowService.update_status(
            reservation_id,
            "conditions_rejected"
        )

    @staticmethod
    def mark_waiting_for_offer_selection(reservation_id):
        """
        Move a reservation to the offer selection step.

        Args:
            reservation_id (int): Reservation identifier.

        Returns:
            Reservation | None
        """

        return WorkflowService.update_status(
            reservation_id,
            "waiting_offer_selection"
        )

    @staticmethod
    def mark_offer_selected(reservation_id):
        """
        Mark an offer catalogue as selected.

        Args:
            reservation_id (int): Reservation identifier.

        Returns:
            Reservation | None
        """

        return WorkflowService.update_status(
            reservation_id,
            "offer_selected"
        )

    @staticmethod
    def mark_confirmed(reservation_id):
        """
        Mark a reservation as fully confirmed.

        Args:
            reservation_id (int): Reservation identifier.

        Returns:
            Reservation | None
        """

        return WorkflowService.update_status(
            reservation_id,
            "confirmed"
        )

    @staticmethod
    def mark_cancelled(reservation_id):
        """
        Cancel a reservation.

        Args:
            reservation_id (int): Reservation identifier.

        Returns:
            Reservation | None
        """

        return WorkflowService.update_status(
            reservation_id,
            "cancelled"
        )
