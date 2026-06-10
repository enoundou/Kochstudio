from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, UTC

datetime.now(UTC)

db = SQLAlchemy()


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False, unique=True)
    phone = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )


class EventType(db.Model):
    __tablename__ = "event_types"

    code = db.Column(db.Text, primary_key=True)
    name_de = db.Column(db.Text, nullable=False)
    name_en = db.Column(db.Text, nullable=False)
    description_de = db.Column(db.Text)
    description_en = db.Column(db.Text)
    active = db.Column(db.Integer, default=1)


class CookingCourse(db.Model):
    __tablename__ = "cooking_courses"

    id = db.Column(db.Integer, primary_key=True)
    name_de = db.Column(db.Text, nullable=False)
    name_en = db.Column(db.Text, nullable=False)
    description_de = db.Column(db.Text)
    description_en = db.Column(db.Text)
    active = db.Column(db.Integer, default=1)


class ReservationStatus(db.Model):
    __tablename__ = "reservation_statuses"

    code = db.Column(db.Text, primary_key=True)
    name_de = db.Column(db.Text, nullable=False)
    name_en = db.Column(db.Text, nullable=False)
    sort_order = db.Column(db.Integer)
    active = db.Column(db.Integer, default=1)


class WorkflowStep(db.Model):
    __tablename__ = "workflow_steps"

    code = db.Column(db.Text, primary_key=True)
    name_de = db.Column(db.Text, nullable=False)
    name_en = db.Column(db.Text, nullable=False)
    sort_order = db.Column(db.Integer)
    active = db.Column(db.Integer, default=1)


class Reservation(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)
    reservation_number = db.Column(db.Text, unique=True, nullable=False)

    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    event_type_code = db.Column(db.Text, db.ForeignKey("event_types.code"), nullable=False)
    cooking_course_id = db.Column(db.Integer, db.ForeignKey("cooking_courses.id"))

    participant_count = db.Column(db.Integer)
    first_choice_date = db.Column(db.Date)
    first_choice_time = db.Column(db.Time)
    second_choice_date = db.Column(db.Date)
    second_choice_time = db.Column(db.Time)
    note = db.Column(db.Text)

    billing_company_name = db.Column(db.Text)
    billing_first_name = db.Column(db.Text)
    billing_last_name = db.Column(db.Text)
    billing_street = db.Column(db.Text)
    billing_house_number = db.Column(db.Text)
    billing_address_line_2 = db.Column(db.Text)
    billing_postal_code = db.Column(db.Text)
    billing_city = db.Column(db.Text)
    billing_state_region = db.Column(db.Text)
    billing_country = db.Column(db.Text)

    status_code = db.Column(
        db.Text,
        db.ForeignKey("reservation_statuses.code"),
        nullable=False,
        default="temporary"
    )
    current_step_code = db.Column(db.Text, db.ForeignKey("workflow_steps.code"))

    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    confirmed_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)

    customer = db.relationship("Customer", backref="reservations")
    event_type = db.relationship("EventType")
    cooking_course = db.relationship("CookingCourse")
    status = db.relationship("ReservationStatus")
    current_step = db.relationship("WorkflowStep")


class ReservationCondition(db.Model):
    __tablename__ = "reservation_conditions"

    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey("reservations.id"), nullable=False)
    sent_at = db.Column(db.DateTime)
    responded_at = db.Column(db.DateTime)
    is_accepted = db.Column(db.Integer)
    confirmation_token = db.Column(db.Text, unique=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))

    reservation = db.relationship("Reservation", backref="conditions")


class OfferCatalogue(db.Model):
    __tablename__ = "offer_catalogues"

    id = db.Column(db.Integer, primary_key=True)
    name_de = db.Column(db.Text, nullable=False)
    name_en = db.Column(db.Text, nullable=False)
    description_de = db.Column(db.Text)
    description_en = db.Column(db.Text)
    pdf_url = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2))
    active = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))


class ReservationOfferSelection(db.Model):
    __tablename__ = "reservation_offer_selections"

    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey("reservations.id"), nullable=False)
    catalogue_id = db.Column(db.Integer, db.ForeignKey("offer_catalogues.id"), nullable=False)
    selected_at = db.Column(db.DateTime)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))

    reservation = db.relationship("Reservation", backref="offer_selections")
    catalogue = db.relationship("OfferCatalogue")


class EmailType(db.Model):
    __tablename__ = "email_types"

    code = db.Column(db.Text, primary_key=True)
    name_de = db.Column(db.Text, nullable=False)
    name_en = db.Column(db.Text, nullable=False)
    active = db.Column(db.Integer, default=1)


class EmailStatus(db.Model):
    __tablename__ = "email_statuses"

    code = db.Column(db.Text, primary_key=True)
    name_de = db.Column(db.Text, nullable=False)
    name_en = db.Column(db.Text, nullable=False)
    active = db.Column(db.Integer, default=1)


class EmailLog(db.Model):
    __tablename__ = "email_logs"

    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey("reservations.id"), nullable=False)
    email_type_code = db.Column(db.Text, db.ForeignKey("email_types.code"), nullable=False)
    to_email = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime)
    status_code = db.Column(db.Text, db.ForeignKey("email_statuses.code"), nullable=False)
    subject = db.Column(db.Text)
    body = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))

    reservation = db.relationship("Reservation", backref="email_logs")
    email_type = db.relationship("EmailType")
    status = db.relationship("EmailStatus")


class AutomationJobType(db.Model):
    __tablename__ = "automation_job_types"

    code = db.Column(db.Text, primary_key=True)
    name_de = db.Column(db.Text, nullable=False)
    name_en = db.Column(db.Text, nullable=False)
    description_de = db.Column(db.Text)
    description_en = db.Column(db.Text)
    active = db.Column(db.Integer, default=1)


class JobStatus(db.Model):
    __tablename__ = "job_statuses"

    code = db.Column(db.Text, primary_key=True)
    name_de = db.Column(db.Text, nullable=False)
    name_en = db.Column(db.Text, nullable=False)
    active = db.Column(db.Integer, default=1)


class AutomationJob(db.Model):
    __tablename__ = "automation_jobs"

    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey("reservations.id"), nullable=False)
    job_type_code = db.Column(db.Text, db.ForeignKey("automation_job_types.code"), nullable=False)
    scheduled_at = db.Column(db.DateTime)
    executed_at = db.Column(db.DateTime)
    status_code = db.Column(db.Text, db.ForeignKey("job_statuses.code"), nullable=False)
    attempts = db.Column(db.Integer, default=0)
    last_error = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))

    reservation = db.relationship("Reservation", backref="automation_jobs")
    job_type = db.relationship("AutomationJobType")
    status = db.relationship("JobStatus")


class Manager(db.Model):
    __tablename__ = "managers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))


class InvitationStatus(db.Model):
    __tablename__ = "invitation_statuses"

    code = db.Column(db.Text, primary_key=True)
    name_de = db.Column(db.Text, nullable=False)
    name_en = db.Column(db.Text, nullable=False)
    active = db.Column(db.Integer, default=1)


class CalendarInvitation(db.Model):
    __tablename__ = "calendar_invitations"

    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey("reservations.id"), nullable=False)
    invitee_email = db.Column(db.Text, nullable=False)
    invitee_name = db.Column(db.Text)
    calendar_event_id = db.Column(db.Text)
    sent_at = db.Column(db.DateTime)
    status_code = db.Column(db.Text, db.ForeignKey("invitation_statuses.code"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))

    reservation = db.relationship("Reservation", backref="calendar_invitations")
    status = db.relationship("InvitationStatus")


class Collaborator(db.Model):
    __tablename__ = "collaborators"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False)
    role = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))


class InvitationCollaborator(db.Model):
    __tablename__ = "invitation_collaborators"

    id = db.Column(db.Integer, primary_key=True)
    invitation_id = db.Column(db.Integer, db.ForeignKey("calendar_invitations.id"), nullable=False)
    collaborator_id = db.Column(db.Integer, db.ForeignKey("collaborators.id"), nullable=False)
    responded_at = db.Column(db.DateTime)
    status_code = db.Column(db.Text, db.ForeignKey("invitation_statuses.code"), nullable=False)

    invitation = db.relationship("CalendarInvitation", backref="collaborators")
    collaborator = db.relationship("Collaborator")
    status = db.relationship("InvitationStatus")