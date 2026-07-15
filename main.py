from sqlalchemy import func
from werkzeug.security import check_password_hash

from app import create_app
from models.models import Manager

app = create_app()

email = "nouneliane@gmail.com".strip().lower()
password = "Eliane"

with app.app_context():
    manager = Manager.query.filter(
        func.lower(func.trim(Manager.email)) == email
    ).first()

    print(manager)

    if manager:
        print(check_password_hash(manager.password_hash, password))