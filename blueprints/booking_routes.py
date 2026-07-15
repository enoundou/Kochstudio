from flask import Blueprint, current_app, jsonify, render_template, request

from models.models import CookingCourse
from services.reservation_service import ReservationService


try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

booking_bp = Blueprint(
    "booking",
    __name__
)


def normalize_email(email):
    """
    Normalize email input before storage.
    """

    return (email or "").strip().lower()


def get_active_courses():
    """
    Return active cooking courses for booking forms.
    """

    return CookingCourse.query.filter_by(active=1).order_by(
        CookingCourse.name_de.asc()
    ).all()


@booking_bp.route("/buchung.html", methods=["GET"])
def booking_form():
    """
    Render the public booking form.
    """

    return render_template(
        "buchung.html",
        cooking_courses=get_active_courses()
    )


@booking_bp.route("/buchung", methods=["POST"])
def submit_booking():
    """
    Create a reservation from a standard HTML form post.
    """

    data = request.form.to_dict()
    data["email"] = normalize_email(data.get("email"))

    try:
        reservation = ReservationService.create_reservation(data)
    except Exception as exc:
        return render_template(
            "buchung.html",
            cooking_courses=get_active_courses(),
            error=str(exc)
        ), 400

    return render_template(
        "booking_success.html",
        reservation=reservation
    )

def extract_openai_text(response):
    """
    Extract text from an OpenAI Responses API result.
    """

    output_text = getattr(response, "output_text", None)

    if output_text:
        return output_text

    parts = []

    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                parts.append(text)

    return "\n".join(parts).strip()


@booking_bp.route("/note/improve", methods=["POST"])
def improve_note_text():
    """
    Improve the public booking note text with OpenAI.
    """

    payload = request.get_json(silent=True) or {}
    note = (payload.get("note") or "").strip()

    if not note:
        return jsonify({
            "error": "Bitte geben Sie zuerst eine Mitteilung ein."
        }), 400

    if OpenAI is None:
        return jsonify({
            "error": "OpenAI ist nicht installiert."
        }), 503

    api_key = current_app.config.get("OPENAI_API_KEY")

    if not api_key:
        return jsonify({
            "error": "OpenAI API-Key ist nicht konfiguriert."
        }), 503

    system_prompt = """
Du verbesserst kurze Kundennachrichten für ein deutsches Kochstudio.
Der Text soll freundlich, klar und professionell klingen.
Bewahre alle Fakten, Namen, Termine, Zahlen und Wünsche.
Erfinde nichts dazu und entferne keine wichtige Information.
Gib nur den verbesserten Text zurück, ohne Betreff und ohne Markdown.
""".strip()

    user_prompt = f"""
Bitte verbessere diese Mitteilung für das Buchungsformular:

{note}
""".strip()

    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=current_app.config.get("OPENAI_MODEL"),
            input=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            max_output_tokens=600,
        )

        improved_text = extract_openai_text(response)

        if not improved_text:
            return jsonify({
                "error": "OpenAI hat keinen Text zurückgegeben."
            }), 502

        return jsonify({
            "text": improved_text.strip()
        })

    except Exception as exc:
        current_app.logger.warning(
            f"OpenAI note improvement failed: {exc}"
        )
        return jsonify({
            "error": "Der Text konnte gerade nicht verbessert werden."
        }), 502
