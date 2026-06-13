from flask import Blueprint, jsonify, request

from models import (
    db,
    Reservation,
    EmailLog,
    AutomationJob,
    Manager,
    Collaborator
)
from services.automation_service import AutomationService
from services.workflow_service import WorkflowService


admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/api/admin"
)


@admin_bp.route("/dashboard", methods=["GET"])
def dashboard():
    """
    Retrieve dashboard metrics for the admin panel.
    """

    return jsonify({
        "reservations_total": Reservation.query.count(),
        "reservations_temporary": Reservation.query.filter_by(
            status_code="temporary"
        ).count(),
        "reservations_confirmed": Reservation.query.filter_by(
            status_code="confirmed"
        ).count(),
        "reservations_cancelled": Reservation.query.filter_by(
            status_code="cancelled"
        ).count(),
        "pending_jobs": AutomationJob.query.filter_by(
            status_code="scheduled"
        ).count(),
        "failed_jobs": AutomationJob.query.filter_by(
            status_code="failed"
        ).count(),
        "failed_emails": EmailLog.query.filter_by(
            status_code="failed"
        ).count()
    })


@admin_bp.route("/jobs/run", methods=["POST"])
def run_jobs_manually():
    """
    Manually execute all pending automation jobs.

    Useful for testing, local development, or admin-triggered
    workflow execution.
    """

    processed_count = AutomationService.run_pending_jobs()

    return jsonify({
        "success": True,
        "processed_jobs": processed_count
    })


@admin_bp.route("/jobs", methods=["GET"])
def get_jobs():
    """
    Retrieve automation jobs for monitoring.
    """

    jobs = AutomationJob.query.order_by(
        AutomationJob.created_at.desc()
    ).limit(100).all()

    return jsonify([
        {
            "id": job.id,
            "reservation_id": job.reservation_id,
            "job_type_code": job.job_type_code,
            "status_code": job.status_code,
            "scheduled_at": (
                job.scheduled_at.isoformat()
                if job.scheduled_at
                else None
            ),
            "executed_at": (
                job.executed_at.isoformat()
                if job.executed_at
                else None
            ),
            "attempts": job.attempts,
            "last_error": job.last_error
        }
        for job in jobs
    ])


@admin_bp.route("/reservations/<int:reservation_id>/status", methods=["PATCH"])
def update_reservation_status(reservation_id):
    """
    Update reservation status from the admin panel.
    """

    data = request.get_json()
    new_status = data.get("status_code")

    if not new_status:
        return jsonify({
            "success": False,
            "message": "status_code is required."
        }), 400

    try:
        reservation = WorkflowService.update_status(
            reservation_id,
            new_status
        )

        if not reservation:
            return jsonify({
                "success": False,
                "message": "Reservation not found."
            }), 404

        return jsonify({
            "success": True,
            "reservation_id": reservation.id,
            "status_code": reservation.status_code
        })

    except ValueError as exc:
        return jsonify({
            "success": False,
            "message": str(exc)
        }), 400


@admin_bp.route("/email-logs", methods=["GET"])
def get_email_logs():
    """
    Retrieve recent email logs.
    """

    logs = EmailLog.query.order_by(
        EmailLog.created_at.desc()
    ).limit(100).all()

    return jsonify([
        {
            "id": log.id,
            "reservation_id": log.reservation_id,
            "email_type_code": log.email_type_code,
            "to_email": log.to_email,
            "status_code": log.status_code,
            "subject": log.subject,
            "sent_at": (
                log.sent_at.isoformat()
                if log.sent_at
                else None
            ),
            "created_at": (
                log.created_at.isoformat()
                if log.created_at
                else None
            )
        }
        for log in logs
    ])


@admin_bp.route("/managers", methods=["GET"])
def get_managers():
    """
    Retrieve all managers.
    """

    managers = Manager.query.all()

    return jsonify([
        {
            "id": manager.id,
            "name": manager.name,
            "email": manager.email
        }
        for manager in managers
    ])


@admin_bp.route("/managers", methods=["POST"])
def create_manager():
    """
    Create a manager record.
    """

    data = request.get_json()

    manager = Manager(
        name=data["name"],
        email=data["email"]
    )

    db.session.add(manager)
    db.session.commit()

    return jsonify({
        "success": True,
        "manager_id": manager.id
    }), 201


@admin_bp.route("/collaborators", methods=["GET"])
def get_collaborators():
    """
    Retrieve all collaborators.
    """

    collaborators = Collaborator.query.all()

    return jsonify([
        {
            "id": collaborator.id,
            "name": collaborator.name,
            "email": collaborator.email,
            "role": collaborator.role
        }
        for collaborator in collaborators
    ])


@admin_bp.route("/collaborators", methods=["POST"])
def create_collaborator():
    """
    Create a collaborator record.
    """

    data = request.get_json()

    collaborator = Collaborator(
        name=data["name"],
        email=data["email"],
        role=data.get("role")
    )

    db.session.add(collaborator)
    db.session.commit()

    return jsonify({
        "success": True,
        "collaborator_id": collaborator.id
    }), 201