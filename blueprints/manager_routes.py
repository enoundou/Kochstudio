from flask import Blueprint, redirect, render_template, request, session, url_for
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from models.models import (
    db,
    AutomationJob,
    EmailLog,
    Manager,
    Reservation,
    CookingCourse,
    CoursePriceCategory,
)
from services.automation_service import AutomationService
from services.reservation_service import ReservationService


manager_bp = Blueprint(
    "manager",
    __name__
)


def normalize_email(email):
    """
    Normalize email input before lookup or storage.
    """

    return (email or "").strip().lower()


def find_manager_by_email(email):
    """
    Find a manager using case-insensitive email matching.
    """

    normalized_email = normalize_email(email)

    if not normalized_email:
        return None

    return Manager.query.filter(
        func.lower(func.trim(Manager.email)) == normalized_email
    ).first()


def get_current_manager():
    """
    Return the manager for the active session.
    """

    manager_id = session.get("manager_id")

    if not manager_id:
        return None

    return db.session.get(
        Manager,
        manager_id
    )


@manager_bp.route("/manager.html", methods=["GET"])
@manager_bp.route("/manager", methods=["GET"])
def manager_page():
    """
    Render login/register or the protected manager dashboard.
    """

    manager = get_current_manager()

    if not manager:
        return render_template(
            "manager_login.html",
            error=request.args.get("error"),
            message=request.args.get("message")
        )

    statistics = {
        "reservations_total": Reservation.query.count(),
        "reservations_temporary": Reservation.query.filter_by(
            status_code="temporary"
        ).count(),
        "reservations_confirmed": Reservation.query.filter_by(
            status_code="confirmed"
        ).count(),
        "pending_jobs": AutomationJob.query.filter_by(
            status_code="scheduled"
        ).count(),
    }

    reservations = Reservation.query.order_by(
        Reservation.created_at.desc()
    ).all()
    jobs = AutomationJob.query.order_by(
        AutomationJob.created_at.desc()
    ).limit(100).all()
    email_logs = EmailLog.query.order_by(
        EmailLog.created_at.desc()
    ).limit(100).all()
    courses = CookingCourse.query.order_by(
        CookingCourse.name_de.asc()
    ).all()
    price_categories = CoursePriceCategory.query.order_by(
        CoursePriceCategory.cooking_course_id.asc(),
        CoursePriceCategory.min_participants.asc(),
        CoursePriceCategory.category_code.asc()
    ).all()

    return render_template(
        "dashboard.html",
        manager=manager,
        statistics=statistics,
        reservations=reservations,
        jobs=jobs,
        email_logs=email_logs,
        courses=courses,
        price_categories=price_categories,
        message=request.args.get("message")
    )


@manager_bp.route("/manager/register", methods=["POST"])
def register():
    """
    Register a manager from a standard HTML form post.
    """

    name = (request.form.get("name") or "").strip()
    email = normalize_email(request.form.get("email"))
    password = request.form.get("password") or ""

    if not name or not email or not password:
        return redirect(url_for(
            "manager.manager_page",
            error="Name, E-Mail und Passwort sind erforderlich."
        ))

    if len(password) < 6:
        return redirect(url_for(
            "manager.manager_page",
            error="Das Passwort muss mindestens 6 Zeichen haben."
        ))

    manager = find_manager_by_email(email)

    if manager and manager.password_hash:
        return redirect(url_for(
            "manager.manager_page",
            error="Dieser Manager ist bereits registriert. Bitte einloggen."
        ))

    if manager:
        manager.name = name
        manager.email = email
        manager.password_hash = generate_password_hash(password)
    else:
        manager = Manager(
            name=name,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(manager)

    db.session.commit()
    session["manager_id"] = manager.id

    return redirect(url_for("manager.manager_page"))


@manager_bp.route("/manager/login", methods=["POST"])
def login():
    """
    Log in a manager from a standard HTML form post.
    """

    email = normalize_email(request.form.get("email"))
    password = request.form.get("password") or ""
    manager = find_manager_by_email(email)

    if not manager or not manager.password_hash:
        return redirect(url_for(
            "manager.manager_page",
            error="E-Mail oder Passwort ist falsch."
        ))

    if not check_password_hash(manager.password_hash, password):
        return redirect(url_for(
            "manager.manager_page",
            error="E-Mail oder Passwort ist falsch."
        ))

    session["manager_id"] = manager.id

    return redirect(url_for("manager.manager_page"))


@manager_bp.route("/manager/logout", methods=["POST"])
def logout():
    """
    Log out the current manager.
    """

    session.pop("manager_id", None)

    return redirect(url_for("manager.manager_page"))


@manager_bp.route("/manager/jobs/run", methods=["POST"])
def run_jobs():
    """
    Run due automation jobs from the manager dashboard.
    """

    if not get_current_manager():
        return redirect(url_for(
            "manager.manager_page",
            error="Bitte zuerst einloggen."
        ))

    count = AutomationService.run_pending_jobs()

    return redirect(url_for(
        "manager.manager_page",
        message=f"{count} Job(s) verarbeitet."
    ))


@manager_bp.route(
    "/manager/reservations/<int:reservation_id>/confirm",
    methods=["POST"]
)
def confirm_reservation(reservation_id):
    """
    Confirm a reservation from the manager dashboard.
    """

    if not get_current_manager():
        return redirect(url_for(
            "manager.manager_page",
            error="Bitte zuerst einloggen."
        ))

    ReservationService.confirm_reservation(reservation_id)

    return redirect(url_for(
        "manager.manager_page",
        message="Buchung bestätigt."
    ))


@manager_bp.route(
    "/manager/reservations/<int:reservation_id>/cancel",
    methods=["POST"]
)
def cancel_reservation(reservation_id):
    """
    Cancel a reservation from the manager dashboard.
    """

    if not get_current_manager():
        return redirect(url_for(
            "manager.manager_page",
            error="Bitte zuerst einloggen."
        ))

    ReservationService.cancel_reservation(reservation_id)

    return redirect(url_for(
        "manager.manager_page",
        message="Buchung storniert."
    ))

@manager_bp.route("/manager/courses/create", methods=["POST"])
def create_course():
    """
    Create a cooking course from the manager dashboard.
    """

    if not get_current_manager():
        return redirect(url_for(
            "manager.manager_page",
            error="Bitte zuerst einloggen."
        ))

    name_de = (request.form.get("name_de") or "").strip()
    description_de = (request.form.get("description_de") or "").strip()

    if not name_de:
        return redirect(url_for(
            "manager.manager_page",
            message="Kochkurs benötigt einen Namen."
        ))

    db.session.add(CookingCourse(
        name_de=name_de,
        name_en=name_de,
        description_de=description_de,
        description_en=description_de,
        active=1
    ))
    db.session.commit()

    return redirect(url_for(
        "manager.manager_page",
        message="Kochkurs gespeichert."
    ))


@manager_bp.route("/manager/price-categories/create", methods=["POST"])
def create_price_category():
    """
    Create a participant-based price category for a cooking course.
    """

    if not get_current_manager():
        return redirect(url_for(
            "manager.manager_page",
            error="Bitte zuerst einloggen."
        ))

    category = CoursePriceCategory(
        cooking_course_id=int(request.form.get("cooking_course_id")),
        category_code=(request.form.get("category_code") or "").strip(),
        name_de=(request.form.get("name_de") or "").strip(),
        description_de=(request.form.get("description_de") or "").strip(),
        min_participants=int(request.form.get("min_participants") or 1),
        max_participants=(
            int(request.form.get("max_participants"))
            if request.form.get("max_participants")
            else None
        ),
        price_per_person=float(request.form.get("price_per_person") or 0),
        discount_percent=float(request.form.get("discount_percent") or 0),
        active=1
    )

    db.session.add(category)
    db.session.commit()

    return redirect(url_for(
        "manager.manager_page",
        message="Preiskategorie gespeichert."
    ))