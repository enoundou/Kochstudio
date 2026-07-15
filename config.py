"""
Application configuration.

This module contains all application settings and
environment-specific configuration values.

Environment variables can be used to override the
default values for production deployments.
"""

import os


class Config:
    """
    Base application configuration.
    """

    #
    # Flask
    #
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "change-this-secret-key"
    )

    #
    # Database
    #
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///reservation_system.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    #
    # Application
    #
    APP_NAME = os.getenv(
        "APP_NAME",
        "Reservation System"
    )

    DEBUG = False

    #
    # Email Settings
    #
    MAIL_PROVIDER = os.getenv(
        "MAIL_PROVIDER",
        "smtp"
    )

    MAIL_HOST = os.getenv(
        "MAIL_HOST",
        "localhost"
    )

    MAIL_PORT = int(
        os.getenv(
            "MAIL_PORT",
            587
        )
    )

    MAIL_USERNAME = os.getenv(
        "MAIL_USERNAME",
        ""
    )

    MAIL_PASSWORD = os.getenv(
        "MAIL_PASSWORD",
        ""
    )

    MAIL_USE_TLS = (
            os.getenv(
                "MAIL_USE_TLS",
                "true"
            ).lower() == "true"
    )

    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_DEFAULT_SENDER",
        "noreply@example.com"
    )

    #
    # Automation Jobs in minutes
    #
    JOB_RUNNER_INTERVAL = int(
        os.getenv(
            "JOB_RUNNER_INTERVAL",
            1
        )
    )

    #
    # Reservation Workflow
    #
    CONDITIONS_DELAY_MINUTES = int(
        os.getenv(
            "CONDITIONS_DELAY_MINUTES",
            30
        )
    )

    CONDITIONS_REMINDER_DAYS = int(
        os.getenv(
            "CONDITIONS_REMINDER_DAYS",
            2
        )
    )

    OFFER_REMINDER_DAYS = int(
        os.getenv(
            "OFFER_REMINDER_DAYS",
            2
        )
    )

    #
    # Calendar Integration
    #
    CALENDAR_PROVIDER = os.getenv(
        "CALENDAR_PROVIDER",
        "internal"
    )

    #
    # Logging
    #
    LOG_LEVEL = os.getenv(
        "LOG_LEVEL",
        "INFO"
    )


    #
    # OpenAI Email Text Generation
    #
    OPENAI_API_KEY = os.getenv(
        "OPENAI_API_KEY",
        ""
    )

    OPENAI_MODEL = os.getenv(
        "OPENAI_MODEL",
        "gpt-5.5"
    )

    USE_OPENAI_EMAILS = (
            os.getenv(
                "USE_OPENAI_EMAILS",
                "true"
            ).lower() == "true"
    )

class DevelopmentConfig(Config):
    """
    Development environment configuration.
    """

    DEBUG = True


class TestingConfig(Config):
    """
    Testing environment configuration.
    """

    TESTING = True

    SQLALCHEMY_DATABASE_URI = (
        "sqlite:///:memory:"
    )


class ProductionConfig(Config):
    """
    Production environment configuration.
    """

    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig
}
