from flask import Blueprint, jsonify

from models import (
    EventType,
    CookingCourse,
    ReservationStatus,
    WorkflowStep,
    EmailType,
    EmailStatus,
    AutomationJobType,
    JobStatus,
    InvitationStatus
)

enum_bp = Blueprint(
    "enums",
    __name__,
    url_prefix="/api/enums"
)


def serialize_enum(item):
    """
    Convert an enum-like model instance into a JSON dictionary.
    """

    return {
        "code": item.code,
        "name_de": item.name_de,
        "name_en": item.name_en,
        "active": item.active
    }


@enum_bp.route("/event-types", methods=["GET"])
def get_event_types():
    """
    Retrieve active event types for dropdowns.
    """

    items = EventType.query.filter_by(active=1).all()
    return jsonify([serialize_enum(item) for item in items])


@enum_bp.route("/reservation-statuses", methods=["GET"])
def get_reservation_statuses():
    """
    Retrieve active reservation statuses for dropdowns.
    """

    items = ReservationStatus.query.filter_by(active=1).order_by(
        ReservationStatus.sort_order.asc()
    ).all()

    return jsonify([serialize_enum(item) for item in items])


@enum_bp.route("/workflow-steps", methods=["GET"])
def get_workflow_steps():
    """
    Retrieve active workflow steps for admin views.
    """

    items = WorkflowStep.query.filter_by(active=1).order_by(
        WorkflowStep.sort_order.asc()
    ).all()

    return jsonify([serialize_enum(item) for item in items])


@enum_bp.route("/cooking-courses", methods=["GET"])
def get_cooking_courses():
    """
    Retrieve active cooking courses for dropdowns.
    """

    courses = CookingCourse.query.filter_by(active=1).all()

    return jsonify([
        {
            "id": course.id,
            "name_de": course.name_de,
            "name_en": course.name_en,
            "description_de": course.description_de,
            "description_en": course.description_en,
            "active": course.active
        }
        for course in courses
    ])


@enum_bp.route("/email-types", methods=["GET"])
def get_email_types():
    """
    Retrieve active email types.
    """

    items = EmailType.query.filter_by(active=1).all()
    return jsonify([serialize_enum(item) for item in items])


@enum_bp.route("/email-statuses", methods=["GET"])
def get_email_statuses():
    """
    Retrieve active email statuses.
    """

    items = EmailStatus.query.filter_by(active=1).all()
    return jsonify([serialize_enum(item) for item in items])


@enum_bp.route("/automation-job-types", methods=["GET"])
def get_automation_job_types():
    """
    Retrieve active automation job types.
    """

    items = AutomationJobType.query.filter_by(active=1).all()
    return jsonify([serialize_enum(item) for item in items])


@enum_bp.route("/job-statuses", methods=["GET"])
def get_job_statuses():
    """
    Retrieve active automation job statuses.
    """

    items = JobStatus.query.filter_by(active=1).all()
    return jsonify([serialize_enum(item) for item in items])


@enum_bp.route("/invitation-statuses", methods=["GET"])
def get_invitation_statuses():
    """
    Retrieve active invitation statuses.
    """

    items = InvitationStatus.query.filter_by(active=1).all()
    return jsonify([serialize_enum(item) for item in items])
