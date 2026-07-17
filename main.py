from sqlalchemy import func
from werkzeug.security import check_password_hash
from datetime import datetime, UTC, timedelta
from app import create_app
from models.models import Manager, AutomationJob, AutomationJobType

app = create_app()

email = "nouneliane@gmail.com".strip().lower()
password = "Eliane"

with app.app_context():
    manager = Manager.query.filter(
        func.lower(func.trim(Manager.email)) == email
    ).first()

    job2 = AutomationJob.query.filter().filter()
    print("jobs1",job2)

    jobs1 = AutomationJob.query.filter(
        AutomationJob.scheduled_at <= datetime.now(UTC)
    ).first()
    print("jobs1",jobs1)
    jobs = AutomationJob.query.filter(
            AutomationJob.status_code == "scheduled",
        ).order_by(
            AutomationJob.scheduled_at.asc()
        ).all()

    print(datetime.now(UTC)
)
    print(jobs)