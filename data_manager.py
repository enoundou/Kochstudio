# data_manager.py

from models import db, Customer, Reservation, EmailLog


class DataManager:

    # ---------- Customers ----------

    @staticmethod
    def create_customer(name, email, phone=None):
        customer = Customer(
            name=name,
            email=email,
            phone=phone
        )

        db.session.add(customer)
        db.session.commit()

        return customer

    @staticmethod
    def get_customer(customer_id):
        return Customer.query.get(customer_id)

    @staticmethod
    def get_customer_by_email(email):
        return Customer.query.filter_by(email=email).first()

    # ---------- Reservations ----------

    @staticmethod
    def create_reservation(
        reservation_number,
        customer_id,
        event_type_code,
        cooking_course_id=None,
        participant_count=None,
        note=None
    ):
        reservation = Reservation(
            reservation_number=reservation_number,
            customer_id=customer_id,
            event_type_code=event_type_code,
            cooking_course_id=cooking_course_id,
            participant_count=participant_count,
            note=note
        )

        db.session.add(reservation)
        db.session.commit()

        return reservation

    @staticmethod
    def get_reservation(reservation_id):
        return Reservation.query.get(reservation_id)

    @staticmethod
    def get_all_reservations():
        return Reservation.query.order_by(
            Reservation.created_at.desc()
        ).all()

    @staticmethod
    def update_reservation_status(
        reservation_id,
        status_code
    ):
        reservation = Reservation.query.get(reservation_id)

        if reservation:
            reservation.status_code = status_code
            db.session.commit()

        return reservation

    # ---------- Email Logs ----------

    @staticmethod
    def log_email(
        reservation_id,
        email_type_code,
        to_email,
        status_code,
        subject=None,
        body=None
    ):
        email_log = EmailLog(
            reservation_id=reservation_id,
            email_type_code=email_type_code,
            to_email=to_email,
            status_code=status_code,
            subject=subject,
            body=body
        )

        db.session.add(email_log)
        db.session.commit()

        return email_log

    # ---------- Generic ----------

    @staticmethod
    def save():
        db.session.commit()

    @staticmethod
    def rollback():
        db.session.rollback()

    @staticmethod
    def delete(obj):
        db.session.delete(obj)
        db.session.commit()