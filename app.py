
from flask import Flask

from models import db

from routers.reservation_routes import reservation_bp


def create_app():
    """
    Application factory.

    Creates and configures the Flask application,
    initializes extensions, registers blueprints,
    and prepares the database connection.

    Returns:
        Flask:
            Configured Flask application instance.
    """

    app = Flask(__name__)

    #
    # Database configuration
    #
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///reservation_system.db"
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    #
    # Initialize database
    #
    db.init_app(app)

    #
    # Register API blueprints
    #
    app.register_blueprint(
        reservation_bp
    )

    #
    # Health check endpoint
    #
    @app.route("/health")
    def health():
        """
        Health check endpoint.

        Returns:
            dict:
                Application health status.
        """

        return {
            "status": "ok",
            "service": "reservation-api"
        }

    #
    # Create database tables
    #
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    """
    Application entry point.

    Starts the Flask development server.
    """

    app = create_app()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
