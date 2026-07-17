from sqlalchemy import text

from dotenv import load_dotenv

load_dotenv()
from flask import Flask

from config import DevelopmentConfig
from models.models import (
    db,
    AutomationJobType,
    Collaborator,
    EmailStatus,
    EmailType,
    EventType,
    InvitationStatus,
    JobStatus,
    Manager,
    CookingCourse,
    CoursePriceCategory,
    ReservationStatus,
    WorkflowStep,
)
from blueprints.booking_routes import booking_bp
from blueprints.customer_workflow_routes import customer_workflow_bp
from blueprints.manager_routes import manager_bp
from blueprints.public_routes import public_bp


def create_app():
    """
    Create and configure the Flask application.
    """

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )
    app.config.from_object(DevelopmentConfig)

    db.init_app(app)

    app.register_blueprint(public_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(manager_bp)
    app.register_blueprint(customer_workflow_bp)

    @app.route("/health")
    def health():
        """
        Return a small health check response.
        """

        return {
            "status": "ok",
            "service": "kochstudio-reservation-system"
        }

    with app.app_context():
        db.create_all()
        ensure_manager_password_column()
        ensure_reservation_course_columns()
        ensure_reservation_offer_selection_columns()
        seed_reference_data()

    return app


def ensure_manager_password_column():
    """
    Add password_hash to existing SQLite manager tables.
    """

    columns = db.session.execute(
        text("PRAGMA table_info(managers)")
    ).fetchall()

    column_names = {
        column[1]
        for column in columns
    }

    if "password_hash" not in column_names:
        db.session.execute(
            text("ALTER TABLE managers ADD COLUMN password_hash TEXT")
        )
        db.session.commit()



def ensure_reservation_course_columns():
    """
    Add course choice columns to existing SQLite reservation tables.
    """

    columns = db.session.execute(
        text("PRAGMA table_info(reservations)")
    ).fetchall()

    column_names = {
        column[1]
        for column in columns
    }

    if "first_choice_course_id" not in column_names:
        db.session.execute(
            text("ALTER TABLE reservations ADD COLUMN first_choice_course_id INTEGER")
        )

    if "second_choice_course_id" not in column_names:
        db.session.execute(
            text("ALTER TABLE reservations ADD COLUMN second_choice_course_id INTEGER")
        )

    db.session.commit()

def ensure_reservation_offer_selection_columns():
    """
    Rebuild reservation offer selections to use course price categories.

    SQLite cannot safely drop a NOT NULL column with ALTER TABLE, so this
    migration rebuilds the table when the old catalogue_id column exists.
    Existing rows are mapped to the first active price category of the
    reservation course when possible.
    """

    columns = db.session.execute(
        text("PRAGMA table_info(reservation_offer_selections)")
    ).fetchall()

    if not columns:
        return

    column_names = {
        column[1]
        for column in columns
    }

    if (
            "course_price_category_id" in column_names
            and "catalogue_id" not in column_names
    ):
        return

    db.session.execute(
        text("ALTER TABLE reservation_offer_selections RENAME TO reservation_offer_selections_old")
    )

    db.session.execute(text("""
        CREATE TABLE reservation_offer_selections (
            id INTEGER PRIMARY KEY,
            reservation_id INTEGER NOT NULL,
            course_price_category_id INTEGER NOT NULL,
            selected_at DATETIME,
            note TEXT,
            created_at DATETIME,
            FOREIGN KEY(reservation_id) REFERENCES reservations(id),
            FOREIGN KEY(course_price_category_id) REFERENCES course_price_categories(id)
        )
    """))

    if "course_price_category_id" in column_names:
        db.session.execute(text("""
            INSERT INTO reservation_offer_selections (
                id,
                reservation_id,
                course_price_category_id,
                selected_at,
                note,
                created_at
            )
            SELECT
                id,
                reservation_id,
                course_price_category_id,
                selected_at,
                note,
                created_at
            FROM reservation_offer_selections_old
            WHERE course_price_category_id IS NOT NULL
        """))
    else:
        db.session.execute(text("""
            INSERT INTO reservation_offer_selections (
                id,
                reservation_id,
                course_price_category_id,
                selected_at,
                note,
                created_at
            )
            SELECT
                old.id,
                old.reservation_id,
                (
                    SELECT cpc.id
                    FROM course_price_categories cpc
                    JOIN reservations r ON r.id = old.reservation_id
                    WHERE cpc.active = 1
                    AND cpc.cooking_course_id IN (
                        r.first_choice_course_id,
                        r.second_choice_course_id,
                        r.cooking_course_id
                    )
                    ORDER BY cpc.price_per_person ASC
                    LIMIT 1
                ),
                old.selected_at,
                old.note,
                old.created_at
            FROM reservation_offer_selections_old old
            WHERE (
                SELECT cpc.id
                FROM course_price_categories cpc
                JOIN reservations r ON r.id = old.reservation_id
                WHERE cpc.active = 1
                AND cpc.cooking_course_id IN (
                    r.first_choice_course_id,
                    r.second_choice_course_id,
                    r.cooking_course_id
                )
                ORDER BY cpc.price_per_person ASC
                LIMIT 1
            ) IS NOT NULL
        """))

    db.session.execute(
        text("DROP TABLE reservation_offer_selections_old")
    )
    db.session.commit()

def ensure_reservation_offer_selection_columns():
    """
    Rebuild reservation offer selections to use course price categories.

    SQLite cannot safely drop a NOT NULL column with ALTER TABLE, so this
    migration rebuilds the table when the old catalogue_id column exists.
    Existing rows are mapped to the first active price category of the
    reservation course when possible.
    """

    columns = db.session.execute(
        text("PRAGMA table_info(reservation_offer_selections)")
    ).fetchall()

    if not columns:
        return

    column_names = {
        column[1]
        for column in columns
    }

    if (
            "course_price_category_id" in column_names
            and "catalogue_id" not in column_names
    ):
        return

    db.session.execute(
        text("ALTER TABLE reservation_offer_selections RENAME TO reservation_offer_selections_old")
    )

    db.session.execute(text("""
        CREATE TABLE reservation_offer_selections (
            id INTEGER PRIMARY KEY,
            reservation_id INTEGER NOT NULL,
            course_price_category_id INTEGER NOT NULL,
            selected_at DATETIME,
            note TEXT,
            created_at DATETIME,
            FOREIGN KEY(reservation_id) REFERENCES reservations(id),
            FOREIGN KEY(course_price_category_id) REFERENCES course_price_categories(id)
        )
    """))

    if "course_price_category_id" in column_names:
        db.session.execute(text("""
            INSERT INTO reservation_offer_selections (
                id,
                reservation_id,
                course_price_category_id,
                selected_at,
                note,
                created_at
            )
            SELECT
                id,
                reservation_id,
                course_price_category_id,
                selected_at,
                note,
                created_at
            FROM reservation_offer_selections_old
            WHERE course_price_category_id IS NOT NULL
        """))
    else:
        db.session.execute(text("""
            INSERT INTO reservation_offer_selections (
                id,
                reservation_id,
                course_price_category_id,
                selected_at,
                note,
                created_at
            )
            SELECT
                old.id,
                old.reservation_id,
                (
                    SELECT cpc.id
                    FROM course_price_categories cpc
                    JOIN reservations r ON r.id = old.reservation_id
                    WHERE cpc.active = 1
                    AND cpc.cooking_course_id IN (
                        r.first_choice_course_id,
                        r.second_choice_course_id,
                        r.cooking_course_id
                    )
                    ORDER BY cpc.price_per_person ASC
                    LIMIT 1
                ),
                old.selected_at,
                old.note,
                old.created_at
            FROM reservation_offer_selections_old old
            WHERE (
                SELECT cpc.id
                FROM course_price_categories cpc
                JOIN reservations r ON r.id = old.reservation_id
                WHERE cpc.active = 1
                AND cpc.cooking_course_id IN (
                    r.first_choice_course_id,
                    r.second_choice_course_id,
                    r.cooking_course_id
                )
                ORDER BY cpc.price_per_person ASC
                LIMIT 1
            ) IS NOT NULL
        """))

    db.session.execute(
        text("DROP TABLE reservation_offer_selections_old")
    )
    db.session.commit()

def ensure_reservation_offer_selection_columns():
    """
    Rebuild reservation offer selections to use course price categories.

    SQLite cannot safely drop a NOT NULL column with ALTER TABLE, so this
    migration rebuilds the table when the old catalogue_id column exists.
    Existing rows are mapped to the first active price category of the
    reservation course when possible.
    """

    columns = db.session.execute(
        text("PRAGMA table_info(reservation_offer_selections)")
    ).fetchall()

    if not columns:
        return

    column_names = {
        column[1]
        for column in columns
    }

    if (
            "course_price_category_id" in column_names
            and "catalogue_id" not in column_names
    ):
        return

    db.session.execute(
        text("ALTER TABLE reservation_offer_selections RENAME TO reservation_offer_selections_old")
    )

    db.session.execute(text("""
        CREATE TABLE reservation_offer_selections (
            id INTEGER PRIMARY KEY,
            reservation_id INTEGER NOT NULL,
            course_price_category_id INTEGER NOT NULL,
            selected_at DATETIME,
            note TEXT,
            created_at DATETIME,
            FOREIGN KEY(reservation_id) REFERENCES reservations(id),
            FOREIGN KEY(course_price_category_id) REFERENCES course_price_categories(id)
        )
    """))

    if "course_price_category_id" in column_names:
        db.session.execute(text("""
            INSERT INTO reservation_offer_selections (
                id,
                reservation_id,
                course_price_category_id,
                selected_at,
                note,
                created_at
            )
            SELECT
                id,
                reservation_id,
                course_price_category_id,
                selected_at,
                note,
                created_at
            FROM reservation_offer_selections_old
            WHERE course_price_category_id IS NOT NULL
        """))
    else:
        db.session.execute(text("""
            INSERT INTO reservation_offer_selections (
                id,
                reservation_id,
                course_price_category_id,
                selected_at,
                note,
                created_at
            )
            SELECT
                old.id,
                old.reservation_id,
                (
                    SELECT cpc.id
                    FROM course_price_categories cpc
                    JOIN reservations r ON r.id = old.reservation_id
                    WHERE cpc.active = 1
                    AND cpc.cooking_course_id IN (
                        r.first_choice_course_id,
                        r.second_choice_course_id,
                        r.cooking_course_id
                    )
                    ORDER BY cpc.price_per_person ASC
                    LIMIT 1
                ),
                old.selected_at,
                old.note,
                old.created_at
            FROM reservation_offer_selections_old old
            WHERE (
                SELECT cpc.id
                FROM course_price_categories cpc
                JOIN reservations r ON r.id = old.reservation_id
                WHERE cpc.active = 1
                AND cpc.cooking_course_id IN (
                    r.first_choice_course_id,
                    r.second_choice_course_id,
                    r.cooking_course_id
                )
                ORDER BY cpc.price_per_person ASC
                LIMIT 1
            ) IS NOT NULL
        """))

    db.session.execute(
        text("DROP TABLE reservation_offer_selections_old")
    )
    db.session.commit()

def seed_reference_data():
    """
    Insert required lookup and demo records if they are missing.
    """

    seed_event_types()
    seed_reservation_statuses()
    seed_workflow_steps()
    seed_email_types()
    seed_email_statuses()
    seed_job_types()
    seed_job_statuses()
    seed_invitation_statuses()
    seed_cooking_courses()
    seed_course_price_categories()
    seed_team_records()

    db.session.commit()


def seed_event_types():
    """
    Insert public event type values.
    """

    items = [
        ("company_event", "Firmenveranstaltung", "Company Event"),
        ("cooking_experience", "Koch-Erlebnisparty", "Cooking Experience"),
        ("kids_event", "Kinderveranstaltung", "Kids Event"),
        ("other", "Sonstiges", "Other"),
    ]

    for code, name_de, name_en in items:
        if not db.session.get(EventType, code):
            db.session.add(EventType(
                code=code,
                name_de=name_de,
                name_en=name_en
            ))


def seed_reservation_statuses():
    """
    Insert reservation workflow status values.
    """
    items = [
        ("temporary", "Vorläufig", "Temporary", 1),
        ("waiting_conditions_confirmation", "Bedingungen offen", "Waiting Conditions", 2),
        ("conditions_confirmed", "Bedingungen bestätigt", "Conditions Confirmed", 3),
        ("conditions_rejected", "Bedingungen abgelehnt", "Conditions Rejected", 4),
        ("waiting_offer_selection", "Angebotswahl offen", "Waiting Offer Selection", 5),
        ("offer_selected", "Angebot ausgewählt", "Offer Selected", 6),
        ("confirmed", "Bestätigt", "Confirmed", 7),
        ("cancelled", "Storniert", "Cancelled", 8),
    ]


    for code, name_de, name_en, sort_order in items:
        if not db.session.get(ReservationStatus, code):
            db.session.add(ReservationStatus(
                code=code,
                name_de=name_de,
                name_en=name_en,
                sort_order=sort_order
            ))


def seed_workflow_steps():
    """
    Insert workflow step values.
    """

    items = [
        ("reservation_received", "Buchung erfasst", "Reservation Received", 1),
        ("waiting_conditions_confirmation", "Bedingungen offen", "Waiting Conditions", 2),
        ("conditions_confirmed", "Bedingungen bestätigt", "Conditions Confirmed", 3),
        ("waiting_offer_selection", "Angebotswahl offen", "Waiting Offer Selection", 4),
        ("offer_selected", "Angebot gewählt", "Offer Selected", 5),
        ("confirmed", "Endgültig reserviert", "Confirmed", 6),
        ("cancelled", "Storniert", "Cancelled", 7),
    ]

    for code, name_de, name_en, sort_order in items:
        if not db.session.get(WorkflowStep, code):
            db.session.add(WorkflowStep(
                code=code,
                name_de=name_de,
                name_en=name_en,
                sort_order=sort_order
            ))


def seed_email_types():
    """
    Insert email type values.
    """

    items = [
        ("conditions_info", "Bedingungen", "Conditions"),
        ("conditions_reminder", "Erinnerung Bedingungen", "Conditions Reminder"),
        ("offer_catalogue", "Angebote", "Offer Catalogue"),
        ("offer_reminder", "Erinnerung Angebot", "Offer Reminder"),
        ("reservation_confirmed", "Reservierung bestätigt", "Reservation Confirmed"),
        ("manager_invoice_request", "Rechnung erstellen", "Invoice Request"),
        ("collaborator_invitation", "Mitarbeiter Einladung", "Collaborator Invitation"),
    ]

    for code, name_de, name_en in items:
        if not db.session.get(EmailType, code):
            db.session.add(EmailType(
                code=code,
                name_de=name_de,
                name_en=name_en
            ))


def seed_email_statuses():
    """
    Insert email status values.
    """

    items = [
        ("pending", "Ausstehend", "Pending"),
        ("sent", "Gesendet", "Sent"),
        ("failed", "Fehlgeschlagen", "Failed"),
    ]

    for code, name_de, name_en in items:
        if not db.session.get(EmailStatus, code):
            db.session.add(EmailStatus(
                code=code,
                name_de=name_de,
                name_en=name_en
            ))


def seed_job_types():
    """
    Insert automation job type values.
    """

    items = [
        ("send_conditions_after", "Bedingungen senden", "Send Conditions"),
        ("remind_conditions_after", "Bedingungen erinnern", "Remind Conditions"),
        ("send_offer_catalogue", "Angebote senden", "Send Offers"),
        ("remind_offer_after", "Angebot erinnern", "Remind Offer"),
        ("confirm_reservation", "Reservierung bestätigen", "Confirm Reservation"),
        ("notify_manager_invoice", "Manager informieren", "Notify Manager"),
        ("send_calendar_invites", "Mitarbeiter einladen", "Send Calendar Invites"),
    ]

    for code, name_de, name_en in items:
        if not db.session.get(AutomationJobType, code):
            db.session.add(AutomationJobType(
                code=code,
                name_de=name_de,
                name_en=name_en
            ))


def seed_job_statuses():
    """
    Insert automation job status values.
    """
    items = [
        ("scheduled", "Geplant", "Scheduled"),
        ("running", "Läuft", "Running"),
        ("completed", "Abgeschlossen", "Completed"),
        ("failed", "Fehlgeschlagen", "Failed"),
    ]

    for code, name_de, name_en in items:
        if not db.session.get(JobStatus, code):
            db.session.add(JobStatus(
                code=code,
                name_de=name_de,
                name_en=name_en
            ))


def seed_invitation_statuses():
    """
    Insert invitation status values.
    """

    items = [
        ("pending", "Ausstehend", "Pending"),
        ("sent", "Gesendet", "Sent"),
        ("accepted", "Angenommen", "Accepted"),
        ("declined", "Abgelehnt", "Declined"),
    ]

    for code, name_de, name_en in items:
        if not db.session.get(InvitationStatus, code):
            db.session.add(InvitationStatus(
                code=code,
                name_de=name_de,
                name_en=name_en
            ))


def seed_cooking_courses():
    """
    Insert starter cooking courses.
    """

    items = [
        ("Klassische Küche", "Classic Cuisine", "Bodenständig und bewährt."),
        ("Italienische Küche", "Italian Cuisine", "Mediterrane Klassiker und gesellige Menüs."),
        ("Mediterrane Küche", "Mediterranean Cuisine", "Frische Zutaten und leichte Gerichte."),
        ("Asiatische Küche", "Asian Cuisine", "Aromatische Gerichte und besondere Zubereitungen."),
        ("Vegetarisch / Vegan", "Vegetarian / Vegan", "Pflanzliche Küche mit saisonalen Zutaten."),
        ("Backen und Dessert", "Baking and Dessert", "Süße Klassiker und moderne Desserts."),
        ("Kinderkochkurs", "Kids Cooking Class", "Kindgerechtes Kochprogramm mit Betreuung."),
    ]

    for name_de, name_en, description_de in items:
        existing_course = CookingCourse.query.filter_by(
            name_de=name_de
        ).first()

        if not existing_course:
            db.session.add(CookingCourse(
                name_de=name_de,
                name_en=name_en,
                description_de=description_de,
                description_en=description_de,
                active=1
            ))


def seed_course_price_categories():
    """
    Insert default participant-based price categories for each course.
    """

    if CoursePriceCategory.query.count() > 0:
        return

    courses = CookingCourse.query.filter_by(active=1).all()

    for course in courses:
        db.session.add_all([
            CoursePriceCategory(
                cooking_course_id=course.id,
                category_code="A",
                name_de="Preiskategorie A",
                description_de="Klassische, regionale oder mediterrane Küche - bodenständig und bewährt.",
                min_participants=1,
                max_participants=20,
                price_per_person=99.00,
                discount_percent=0,
                active=1
            ),
            CoursePriceCategory(
                cooking_course_id=course.id,
                category_code="A_GROUP",
                name_de="Preiskategorie A Gruppenpreis",
                description_de="Klassische, regionale oder mediterrane Küche mit Gruppenrabatt.",
                min_participants=21,
                max_participants=None,
                price_per_person=99.00,
                discount_percent=10,
                active=1
            ),
            CoursePriceCategory(
                cooking_course_id=course.id,
                category_code="B",
                name_de="Preiskategorie B",
                description_de="Internationale oder aufwendigere Menüs mit besonderen Zutaten.",
                min_participants=1,
                max_participants=20,
                price_per_person=109.00,
                discount_percent=0,
                active=1
            ),
            CoursePriceCategory(
                cooking_course_id=course.id,
                category_code="B_GROUP",
                name_de="Preiskategorie B Gruppenpreis",
                description_de="Internationale oder aufwendigere Menüs mit Gruppenrabatt.",
                min_participants=21,
                max_participants=None,
                price_per_person=109.00,
                discount_percent=10,
                active=1
            ),
        ])



def seed_team_records():
    """
    Insert demo manager and collaborator rows.
    """

    if Manager.query.count() == 0:
        db.session.add(Manager(
            name="Kochstudio Manager",
            email="nouneliane@gmail.com"
        ))

    if Collaborator.query.count() == 0:
        db.session.add_all([
            Collaborator(
                name="Service Team",
                email="serviceenohandels@gmail.com",
                role="Service"
            ),
            Collaborator(
                name="Chef Team",
                email="nouniane@hotmail.de",
                role="Kitchen"
            ),
        ])


if __name__ == "__main__":
    create_app().run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )