import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from app import create_app
from models.models import ReservationCondition
from services.reservation_service import ReservationService


def main():
    """
    Send missing offer catalogue emails for accepted reservations.
    """

    app = create_app()

    with app.app_context():
        accepted_conditions = ReservationCondition.query.filter_by(
            is_accepted=1
        ).all()

        sent_count = 0
        skipped_count = 0
        failed_count = 0

        for condition in accepted_conditions:
            reservation = condition.reservation

            if not reservation:
                skipped_count += 1
                continue

            if ReservationService.offer_catalogue_email_sent(reservation.id):
                skipped_count += 1
                continue

            try:
                ReservationService.send_offer_catalogue_now(reservation)
                sent_count += 1
                print(
                    f"Sent offer email for {reservation.reservation_number} "
                    f"to {reservation.customer.email}"
                )
            except Exception as exc:
                failed_count += 1
                print(
                    f"Failed offer email for {reservation.reservation_number}: "
                    f"{exc}"
                )

        print(
            "Summary: "
            f"sent={sent_count}, skipped={skipped_count}, failed={failed_count}"
        )


if __name__ == "__main__":
    main()