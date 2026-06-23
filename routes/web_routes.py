
from flask import Blueprint
from flask import render_template

from models import (
    db,
    Reservation,
    Customer,
    OfferCatalogue,
    AutomationJob
)


web_bp = Blueprint(
    "web",
    __name__
)


@web_bp.route("/")
def dashboard():
    """
    Render the application dashboard.

    Returns:
        HTML dashboard page.
    """

    statistics = {
        "reservations": Reservation.query.count(),
        "customers": Customer.query.count(),
        "offers": OfferCatalogue.query.count(),
        "pending_jobs": AutomationJob.query.filter_by(
            status_code="scheduled"
        ).count()
    }

    return render_template(
        "dashboard.html",
        statistics=statistics
    )


@web_bp.route("/reservations")
def reservations():
    """
    Render the reservation list page.

    Returns:
        HTML reservation list page.
    """

    reservations = Reservation.query.order_by(
        Reservation.created_at.desc()
    ).all()

    return render_template(
        "reservations.html",
        reservations=reservations
    )


@web_bp.route("/reservations/<int:reservation_id>")
def reservation_detail(reservation_id):
    """
    Render the reservation detail page.

    Args:
        reservation_id (int):
            Reservation identifier.

    Returns:
        HTML reservation detail page.
    """

    reservation = db.session.get(
        Reservation,
        reservation_id
    )

    if not reservation:
        return render_template(
            "404.html"
        ), 404

    return render_template(
        "reservation_detail.html",
        reservation=reservation
    )


@web_bp.route("/reservations/new")
def reservation_form():
    """
    Render the public reservation form.

    Returns:
        HTML reservation form page.
    """

    return render_template(
        "reservation_form.html"
    )


@web_bp.route("/customers")
def customers():
    """
    Render the customer list page.

    Returns:
        HTML customer page.
    """

    customers = Customer.query.order_by(
        Customer.created_at.desc()
    ).all()

    return render_template(
        "customers.html",
        customers=customers
    )


@web_bp.route("/offers")
def offers():
    """
    Render the offer catalogue page.

    Returns:
        HTML offers page.
    """

    offers = OfferCatalogue.query.filter_by(
        active=1
    ).all()

    return render_template(
        "offers.html",
        offers=offers
    )


@web_bp.route("/jobs")
def jobs():
    """
    Render the automation jobs page.

    Returns:
        HTML jobs page.
    """

    jobs = AutomationJob.query.order_by(
        AutomationJob.created_at.desc()
    ).limit(100).all()

    return render_template(
        "jobs.html",
        jobs=jobs
    )


@web_bp.route("/health")
def health():
    """
    Render application health information.

    Returns:
        JSON health information.
    """

    return {
        "status": "ok",
        "application": "kochstudio"
    }
