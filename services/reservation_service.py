# services/reservation_service.py

from datetime import datetime, UTC, timedelta
from uuid import uuid4

from flask import current_app

from models.models import (
    db,
    Customer,
    Reservation,
    ReservationCondition,
    ReservationOfferSelection,
    AutomationJob,
    EmailLog,
    CoursePriceCategory,
)


class ReservationService:
    @staticmethod
    def parse_date(value):
        """
        Parse an ISO date string into a date object.
        """

        if not value:
            return None

        if hasattr(value, "isoformat") and not isinstance(value, str):
            return value

        return datetime.strptime(value, "%Y-%m-%d").date()

    @staticmethod
    def parse_time(value):
        """
        Parse an HTML time value into a time object.
        """

        if not value:
            return None

        if hasattr(value, "isoformat") and not isinstance(value, str):
            return value

        return datetime.strptime(value[:5], "%H:%M").time()

    @staticmethod
    def parse_int(value):
        """
        Convert optional numeric form values into integers.
        """

        if value in (None, ""):
            return None

        return int(value)

    @staticmethod
    def create_reservation(data):
        """
        Create a new reservation.
        Workflow:
        1. Find existing customer by email.
        2. Create customer if not found.
        3. Create reservation.
        4. Generate confirmation token.
        5. Schedule conditions email after 30 minutes.

        Returns:
        Reservation: Created reservation object.
        """

        customer = Customer.query.filter_by(
            email=data["email"]
        ).first()

        if not customer:
            customer = Customer(
                name=data["name"],
                email=data["email"],
                phone=data.get("phone")
            )
            db.session.add(customer)
            db.session.flush()
        else:
            customer.name = data["name"]
            customer.phone = data.get("phone", customer.phone)

        conditions_delay = current_app.config.get(
            "CONDITIONS_DELAY_MINUTES",
            10
        )
        print("conditions_delay", conditions_delay)
        reservation = Reservation(
            reservation_number=ReservationService.generate_reservation_number(),
            customer_id=customer.id,
            event_type_code=data["event_type_code"],
            cooking_course_id=ReservationService.parse_int(
                data.get("cooking_course_id")
            ),
            participant_count=ReservationService.parse_int(
                data.get("participant_count")
            ),

            first_choice_date=ReservationService.parse_date(
                data.get("first_choice_date")
            ),
            first_choice_time=ReservationService.parse_time(
                data.get("first_choice_time")
            ),
            first_choice_course_id=ReservationService.parse_int(
                data.get("first_choice_course_id")
            ),
            second_choice_date=ReservationService.parse_date(
                data.get("second_choice_date")
            ),
            second_choice_time=ReservationService.parse_time(
                data.get("second_choice_time")
            ),
            second_choice_course_id=ReservationService.parse_int(
                data.get("second_choice_course_id")
            ),

            note=data.get("note"),

            status_code="temporary",
            current_step_code="reservation_received"
        )

        db.session.add(reservation)
        db.session.flush()

        condition = ReservationCondition(
            reservation_id=reservation.id,
            confirmation_token=str(uuid4()),
            is_accepted=None
        )

        db.session.add(condition)

        job = AutomationJob(
            reservation_id=reservation.id,
            job_type_code="send_conditions_after",
            scheduled_at=datetime.now(UTC) + timedelta(minutes=conditions_delay),
            status_code="scheduled"
        )

        db.session.add(job)

        db.session.commit()

        return reservation


    @staticmethod
    def accept_conditions(token):
        """
        Accept reservation conditions and send the offer catalogue email.

        The offer email is sent immediately after the customer accepts the
        conditions. A scheduled job is kept as a safety net until the email is
        successfully sent.
        """

        condition = ReservationCondition.query.filter_by(
            confirmation_token=token
        ).first()

        if not condition:
            return None

        reservation = condition.reservation

        condition.is_accepted = 1
        condition.responded_at = condition.responded_at or datetime.now(UTC)

        reservation.status_code = "conditions_confirmed"
        reservation.current_step_code = "conditions_confirmed"
        reservation.updated_at = datetime.now(UTC)

        offer_job = AutomationJob.query.filter_by(
            reservation_id=reservation.id,
            job_type_code="send_offer_catalogue",
            status_code="scheduled"
        ).first()

        if not offer_job and not ReservationService.offer_catalogue_email_sent(
                reservation.id
        ):
            offer_job = AutomationJob(
                reservation_id=reservation.id,
                job_type_code="send_offer_catalogue",
                scheduled_at=datetime.now(UTC),
                status_code="scheduled"
            )
            db.session.add(offer_job)

        db.session.commit()

        ReservationService.send_offer_catalogue_now(reservation)

        if offer_job and offer_job.status_code == "scheduled":
            offer_job.status_code = "completed"
            offer_job.executed_at = datetime.now(UTC)
            db.session.commit()

        return reservation
    @staticmethod
    def offer_catalogue_email_sent(reservation_id):
        """
        Return True when an offer catalogue email was sent successfully.
        """

        return EmailLog.query.filter_by(
            reservation_id=reservation_id,
            email_type_code="offer_catalogue",
            status_code="sent"
        ).first() is not None

    @staticmethod
    def schedule_offer_reminder_if_missing(reservation_id):
        """
        Schedule one offer reminder if no pending reminder exists.
        """

        existing_reminder = AutomationJob.query.filter_by(
            reservation_id=reservation_id,
            job_type_code="remind_offer_after",
            status_code="scheduled"
        ).first()

        if existing_reminder:
            return existing_reminder

        reminder_job = AutomationJob(
            reservation_id=reservation_id,
            job_type_code="remind_offer_after",
            scheduled_at=datetime.now(UTC) + timedelta(days=current_app.config.get(
                "OFFER_REMINDER_DAYS",
                2
            )),
            status_code="scheduled"
        )

        db.session.add(reminder_job)

        return reminder_job

    @staticmethod
    def send_offer_catalogue_now(reservation):
        """
        Send the offer catalogue email immediately if it was not sent yet.

        This method does not create an automatic offer reminder job.
        """

        if ReservationService.offer_catalogue_email_sent(reservation.id):
            return

        from services.email_service import EmailService

        EmailService.send_offer_catalogue(reservation)

        reservation.status_code = "waiting_offer_selection"
        reservation.current_step_code = "waiting_offer_selection"
        reservation.updated_at = datetime.now(UTC)

        db.session.commit()

    @staticmethod
    def reject_conditions(token):
        """
        Reject reservation conditions.

        Marks the reservation as cancel
        and records the rejection timestamp.

        Args:
            token (str): Unique confirmation token.

        Returns:
            Reservation | None
        """

        condition = ReservationCondition.query.filter_by(
            confirmation_token=token
        ).first()

        if not condition:
            return None

        reservation = condition.reservation

        condition.is_accepted = 0
        condition.responded_at = datetime.now(UTC)

        reservation.status_code = "cancelled"
        reservation.current_step_code = "conditions_rejected"
        reservation.cancelled_at = datetime.now(UTC)
        reservation.updated_at = datetime.now(UTC)

        db.session.commit()

        return reservation

    @staticmethod
    def select_offer(
            reservation_id,
            course_price_category_id,
            note=None,
            billing_data=None
    ):
        """
        Select a course price category for a reservation.

        The selected offer now points to course_price_categories instead of
        the removed offer_catalogues table.
        """

        reservation = Reservation.query.get(reservation_id)

        if not reservation:
            return None

        selected_category = CoursePriceCategory.query.get(
            ReservationService.parse_int(course_price_category_id)
        )

        if not selected_category or selected_category.active != 1:
            return None

        valid_course_ids = {
            reservation.first_choice_course_id,
            reservation.second_choice_course_id,
            reservation.cooking_course_id,
        }
        valid_course_ids.discard(None)

        if valid_course_ids and selected_category.cooking_course_id not in valid_course_ids:
            return None

        participant_count = reservation.participant_count

        if participant_count:
            if selected_category.min_participants > participant_count:
                return None

            if (
                    selected_category.max_participants is not None
                    and selected_category.max_participants < participant_count
            ):
                return None

        if billing_data:
            ReservationService.apply_billing_address(
                reservation,
                billing_data
            )

        selection = ReservationOfferSelection(
            reservation_id=reservation.id,
            course_price_category_id=selected_category.id,
            selected_at=datetime.now(UTC),
            note=note
        )

        db.session.add(selection)

        reservation.status_code = "offer_selected"
        reservation.current_step_code = "offer_selected"
        reservation.cooking_course_id = selected_category.cooking_course_id
        reservation.updated_at = datetime.now(UTC)

        confirm_job = AutomationJob(
            reservation_id=reservation.id,
            job_type_code="confirm_reservation",
            scheduled_at=datetime.now(UTC),
            status_code="scheduled"
        )

        manager_job = AutomationJob(
            reservation_id=reservation.id,
            job_type_code="notify_manager_invoice",
            scheduled_at=datetime.now(UTC),
            status_code="scheduled"
        )

        calendar_job = AutomationJob(
            reservation_id=reservation.id,
            job_type_code="send_calendar_invites",
            scheduled_at=datetime.now(UTC),
            status_code="scheduled"
        )

        db.session.add_all([
            confirm_job,
            manager_job,
            calendar_job
        ])

        db.session.commit()

        return selection

    @staticmethod
    def confirm_reservation(reservation_id):
        """
        Confirm a reservation and finalize the booking process.

        Updates the reservation status to "confirmed", stores the
        confirmation timestamp, and marks the reservation as
        officially booked.

        This method is typically executed after:
        - The customer has accepted the reservation conditions.
        - The customer has selected an offer catalogue.
        - All required booking information has been provided.

        Args:
            reservation_id (int): Reservation identifier.

        Returns:
            Reservation | None:
                The updated reservation object if found,
                otherwise None.
        """

        reservation = Reservation.query.get(reservation_id)

        if not reservation:
            return None

        if reservation.status_code == "confirmed":
            return reservation

        if reservation.status_code == "cancelled":
            return reservation

        reservation.status_code = "confirmed"
        reservation.current_step_code = "confirmed"
        reservation.confirmed_at = datetime.now(UTC)
        reservation.updated_at = datetime.now(UTC)

        db.session.commit()

        from services.email_service import EmailService

        EmailService.send_reservation_confirmation(
            reservation
        )

        return reservation

    @staticmethod
    def cancel_reservation(reservation_id):
        """
        Cancel a reservation.

        Updates the reservation status to "cancel" and records
        the cancellation timestamp. This method can be triggered
        manually by an administrator or automatically by the
        reservation workflow.

        Typical scenarios:
        - Customer rejects the reservation conditions.
        - Customer withdraws the booking request.
        - Reservation expires without response.

        Args:
            reservation_id (int): Reservation identifier.

        Returns:
            Reservation | None:
                Updated reservation object or None if the
                reservation does not exist.
        """

        reservation = Reservation.query.get(reservation_id)

        if not reservation:
            return None

        if reservation.status_code == "cancelled":
            return reservation

        reservation.status_code = "cancelled"
        reservation.current_step_code = "cancelled"
        reservation.cancelled_at = datetime.now(UTC)
        reservation.updated_at = datetime.now(UTC)

        db.session.commit()

        return reservation

    @staticmethod
    def update_billing_address(reservation_id, data):
        """
        Update the billing address of a reservation.

        Stores or updates invoice-related address information
        directly in the reservation record.

        Args:
            reservation_id (int): Reservation identifier.
            data (dict): Billing address information.

        Returns:
            Reservation | None:
                Updated reservation object or None if the
                reservation does not exist.
        """

        reservation = Reservation.query.get(reservation_id)

        if not reservation:
            return None

        ReservationService.apply_billing_address(
            reservation,
            data
        )

        reservation.updated_at = datetime.now(UTC)

        db.session.commit()

        return reservation

    @staticmethod
    def apply_billing_address(reservation, data):
        """
        Apply invoice address fields to a reservation instance.
        """

        reservation.billing_company_name = data.get("billing_company_name")
        reservation.billing_first_name = data.get("billing_first_name")
        reservation.billing_last_name = data.get("billing_last_name")
        reservation.billing_street = data.get("billing_street")
        reservation.billing_house_number = data.get("billing_house_number")
        reservation.billing_address_line_2 = data.get("billing_address_line_2")
        reservation.billing_postal_code = data.get("billing_postal_code")
        reservation.billing_city = data.get("billing_city")
        reservation.billing_state_region = data.get("billing_state_region")
        reservation.billing_country = data.get("billing_country")

    @staticmethod
    def schedule_conditions_reminder(reservation_id):
        """
        Schedule a reminder for reservation conditions.

        Creates an automation job that will send a reminder
        to the customer if the reservation conditions have
        not been accepted within the defined timeframe.

        Args:
            reservation_id (int): Reservation identifier.

        Returns:
            AutomationJob:
                Created automation job instance.
        """

        job = AutomationJob(
            reservation_id=reservation_id,
            job_type_code="remind_conditions_after",
            scheduled_at=datetime.now(UTC) + timedelta(days=current_app.config.get(
                "CONDITIONS_REMINDER_DAYS",
                2
            )),
            status_code="scheduled"
        )

        db.session.add(job)
        db.session.commit()

        return job

    @staticmethod
    def schedule_offer_reminder(reservation_id):
        """
        Schedule a reminder for offer selection.

        Creates an automation job that reminds the customer
        to select an offer catalogue if no selection has been
        made within the configured waiting period.

        Args:
            reservation_id (int): Reservation identifier.

        Returns:
            AutomationJob:
                Created automation job instance.
        """

        job = AutomationJob(
            reservation_id=reservation_id,
            job_type_code="remind_offer_after",
            scheduled_at=datetime.now(UTC) + timedelta(days=current_app.config.get(
                "OFFER_REMINDER_DAYS",
                2
            )),
            status_code="scheduled"
        )

        db.session.add(job)
        db.session.commit()

        return job

    @staticmethod
    def generate_reservation_number():
        """
        Generate a unique reservation reference number.

        The generated identifier is used as the primary
        customer-facing booking reference and can be used
        for emails, invoices, reports, and customer support.

        Example:
            RES-20260115-8F3A

        Returns:
        str:
            Reservation reference number.
        """

        today = datetime.now(UTC).strftime("%Y%m%d")
        short_id = uuid4().hex[:4].upper()

        return f"RES-{today}-{short_id}"

    @staticmethod
    def get_reservation(reservation_id):
        """
        Retrieve a reservation by its identifier.

        Args:
            reservation_id (int): Reservation identifier.

        Returns:
            Reservation | None:
                Reservation object if found, otherwise None.
        """

        return Reservation.query.get(reservation_id)

    @staticmethod
    def get_all_reservations():
        """
        Retrieve all reservations.

        Returns:
            list[Reservation]:
                Reservations ordered by creation date, newest first.
        """

        return Reservation.query.order_by(
            Reservation.created_at.desc()
        ).all()
