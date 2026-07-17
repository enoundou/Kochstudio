import json
import smtplib
from email.message import EmailMessage
from datetime import datetime, UTC

from flask import current_app, url_for

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from models.models import (
    db,
    EmailLog,
    Manager,
    Collaborator,
    ReservationCondition,
    CoursePriceCategory,
)


class EmailService:
    """
    Service responsible for sending emails and storing email audit logs.

    Workflow decisions should stay in AutomationService. This service only
    builds and sends the messages that belong to each workflow step.
    """

    @staticmethod
    def send_email(
            reservation,
            email_type_code,
            recipient_email,
            subject,
            body
    ):
        """
        Send an email and create an email log entry.

        The current implementation stores the email in the database and logs
        the send action. A real SMTP, SendGrid, Mailgun or Microsoft Graph
        provider can be connected here later.
        """

        try:
            EmailService.deliver_email(
                recipient_email=recipient_email,
                subject=subject,
                body=body
            )

            current_app.logger.info(
                f"Sent email to {recipient_email}"
            )

            email_log = EmailLog(
                reservation_id=reservation.id,
                email_type_code=email_type_code,
                to_email=recipient_email,
                subject=subject,
                body=body,
                sent_at=datetime.now(UTC),
                status_code="sent"
            )

            db.session.add(email_log)
            db.session.commit()

            return email_log

        except Exception as exc:
            email_log = EmailLog(
                reservation_id=reservation.id,
                email_type_code=email_type_code,
                to_email=recipient_email,
                subject=subject,
                body=body,
                status_code="failed"
            )

            db.session.add(email_log)
            db.session.commit()

            raise exc

    @staticmethod
    def deliver_email(recipient_email, subject, body):
        """
        Deliver an email through the configured SMTP server.

        Set MAIL_PROVIDER=log to disable real sending during local tests.
        """

        provider = current_app.config.get("MAIL_PROVIDER", "smtp").lower()

        if provider in ("log", "database"):
            current_app.logger.info(
                f"Email delivery skipped for {recipient_email}."
            )
            return

        if provider != "smtp":
            raise ValueError(
                f"Unsupported mail provider: {provider}"
            )

        host = current_app.config.get("MAIL_HOST", "")
        port = int(current_app.config.get("MAIL_PORT", 587))
        username = current_app.config.get("MAIL_USERNAME", "")
        password = current_app.config.get("MAIL_PASSWORD", "")
        sender = current_app.config.get("MAIL_DEFAULT_SENDER", "")
        use_tls = current_app.config.get("MAIL_USE_TLS", True)
        use_ssl = current_app.config.get("MAIL_USE_SSL", False)
        timeout = int(current_app.config.get("MAIL_TIMEOUT", 20))

        if not host:
            raise RuntimeError("MAIL_HOST is required for SMTP sending.")

        if not sender:
            raise RuntimeError(
                "MAIL_DEFAULT_SENDER is required for SMTP sending."
            )

        message = EmailMessage()
        message["From"] = sender
        message["To"] = recipient_email
        message["Subject"] = subject
        message.set_content(body)

        if use_ssl:
            with smtplib.SMTP_SSL(
                    host,
                    port,
                    timeout=timeout
            ) as server:
                EmailService.login_and_send(
                    server,
                    username,
                    password,
                    message
                )
            return

        with smtplib.SMTP(
                host,
                port,
                timeout=timeout
        ) as server:
            server.ehlo()

            if use_tls:
                server.starttls()
                server.ehlo()

            EmailService.login_and_send(
                server,
                username,
                password,
                message
            )

    @staticmethod
    def login_and_send(server, username, password, message):
        """
        Log in when credentials are configured, then send the message.
        """

        if username:
            server.login(username, password)

        server.send_message(message)

    @staticmethod
    def send_conditions_email(reservation):
        """
        Send reservation conditions and price information to the customer.

        OpenAI is used only to improve the wording. If OpenAI is not configured
        or returns an error, the local fallback email is sent instead.
        """

        condition = ReservationCondition.query.filter_by(
            reservation_id=reservation.id
        ).first()

        if not condition:
            raise ValueError(
                "ReservationCondition is required before sending conditions."
            )

        accept_url = url_for(
            "customer_workflow.accept_conditions_page",
            token=condition.confirmation_token,
            _external=True
        )
        reject_url = url_for(
            "customer_workflow.reject_conditions_page",
            token=condition.confirmation_token,
            _external=True
        )

        context = EmailService.build_conditions_email_context(
            reservation=reservation,
            accept_url=accept_url,
            reject_url=reject_url
        )

        subject = (
            f"Bedingungen zu Ihrer Buchung "
            f"{reservation.reservation_number}"
        )

        body = (
            EmailService.generate_conditions_email_with_openai(context)
            or EmailService.build_fallback_conditions_email_body(context)
        )

        return EmailService.send_email(
            reservation=reservation,
            email_type_code="conditions_info",
            recipient_email=reservation.customer.email,
            subject=subject,
            body=body
        )


    @staticmethod
    def build_conditions_email_context(reservation, accept_url, reject_url):
        """
        Build structured data for the conditions email prompt and fallback.
        """

        participant_count = reservation.participant_count or 0
        first_course = reservation.first_choice_course
        second_course = reservation.second_choice_course

        first_course_name = (
            first_course.name_de
            if first_course
            else "der gewählte Kochkurs"
        )
        second_course_name = (
            second_course.name_de
            if second_course
            else "der alternative Kochkurs"
        )

        return {
            "customer_name": reservation.customer.name,
            "customer_email": reservation.customer.email,
            "reservation_number": reservation.reservation_number,
            "event_type": reservation.event_type_code,
            "participant_count": participant_count,
            "first_choice_date": EmailService.format_value(
                reservation.first_choice_date,
                "Ihr Wunschtermin"
            ),
            "first_choice_time": EmailService.format_value(
                reservation.first_choice_time,
                "die gewünschte Uhrzeit"
            ),
            "second_choice_date": EmailService.format_value(
                reservation.second_choice_date,
                "Ihr Alternativtermin"
            ),
            "second_choice_time": EmailService.format_value(
                reservation.second_choice_time,
                "die alternative Uhrzeit"
            ),
            "first_course_name": first_course_name,
            "second_course_name": second_course_name,
            "price_lines": EmailService.build_price_lines(
                first_course,
                participant_count
            ),
            "note": reservation.note or "",
            "accept_url": accept_url,
            "reject_url": reject_url,
        }

    @staticmethod
    def generate_conditions_email_with_openai(context):
        """
        Generate a polished German conditions email with OpenAI.

        Returns:
            str | None: Generated email text, or None when local fallback should
            be used.
        """

        if not current_app.config.get("USE_OPENAI_EMAILS", True):
            return None

        api_key = current_app.config.get("OPENAI_API_KEY", "")

        if not api_key or OpenAI is None:
            return None

        model = current_app.config.get("OPENAI_MODEL", "gpt-4.1")

        system_prompt = """
Du bist ein professioneller E-Mail-Assistent für ein deutsches Kochstudio.
Schreibe freundlich, klar, warm und geschäftlich.
Nutze ausschließlich die bereitgestellten Buchungsdaten und den RAG-Kontext.
Erfinde keine Preise, Rabatte, Termine, Verfügbarkeiten oder zusätzlichen Leistungen.
Wenn Informationen fehlen, formuliere neutral.
Gib nur den fertigen E-Mail-Text zurück.
Kein Markdown.
Kein Betreff.

Die Abschnitte "Kosten & Leistungen" und "Ablauf des Kochevents" müssen
immer enthalten sein. Die Leistungen und der Ablauf aus dem RAG-Kontext
müssen sinngemäß vollständig übernommen werden.
""".strip()

        rag_context = """
Leistungen:
In den Preisvarianten sind alle Zutaten, Getränke wie Begrüßungsgetränk,
Wein, Bier, Softdrinks, Tee und Kaffee, Rezepte sowie Kochschürzen enthalten.
Falls für die Gruppengröße ein Gruppenrabatt hinterlegt ist, wird dieser auf
den Gesamtpreis angewendet.

Ablauf des Kochevents:
- Dauer: ca. 4 Stunden
- Begrüßung mit einem Prosecco und kleinem Snack
- Aufteilung in Teams zur Zubereitung der einzelnen Gänge
- Gemeinsames Verzehren der Gerichte
- Abschluss mit einem Dessert
- Danach gemütlicher Ausklang für etwa eine Stunde
""".strip()

        user_prompt = f"""
Erstelle eine Konditions-E-Mail auf Deutsch.

Pflichtstruktur:
1. Persönliche Anrede mit dem Kundennamen
2. Dank für die Anfrage
3. Kurze Zusammenfassung der Anfrage mit Teilnehmeranzahl, Terminen und Kochkursen
4. Abschnitt "Kosten & Leistungen"
5. Abschnitt "Ablauf des Kochevents"
6. Hinweis, dass die Buchung erst nach Bestätigung der Bedingungen vorläufig weitergeführt wird
7. Link zum Akzeptieren der Bedingungen
8. Link zum Ablehnen der Bedingungen
9. Freundliche Schlussformel vom Kochstudio Team

RAG-Kontext:
{rag_context}

Buchungsdaten:
{json.dumps(context, ensure_ascii=False, indent=2)}
""".strip()

        try:
            client = OpenAI(api_key=api_key)
            response = client.responses.create(
                model=model,
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
                max_output_tokens=1400,
            )

            generated_text = EmailService.extract_openai_text(response)

            if not generated_text:
                return None

            return generated_text.strip()

        except Exception as exc:
            current_app.logger.warning(
                f"OpenAI conditions email generation failed: {exc}"
            )
            return None
    @staticmethod
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


    @staticmethod
    def build_fallback_conditions_email_body(context):
        """
        Build the local fallback conditions email.
        """

        participant_label = (
            f"ca. {context['participant_count']} Personen"
            if context["participant_count"]
            else "der angegebenen Teilnehmerzahl"
        )

        body = f"""
Sehr geehrte/r {context['customer_name']},
Kosten & Leistungen:
{context['price_lines']}

In den Preisvarianten sind alle Zutaten, Getränke (Begrüßungsgetränk, Wein, Bier, Softdrinks, Tee und Kaffee), Rezepte sowie Kochschürzen enthalten. 
Falls für Ihre Gruppengröße ein Gruppenrabatt hinterlegt ist, wird dieser auf den Gesamtpreis angewendet.

**Ablauf des Kochevents:**

* Dauer: ca. 4 Stunden
* Begrüßung mit einem Prosecco und kleinem Snack
* Aufteilung in Teams zur Zubereitung der einzelnen Gänge
* Gemeinsames Verzehren der Gerichte
* Abschluss mit einem Dessert
* Danach gemütlicher Ausklang für etwa eine Stunde


Bitte bestätigen Sie die Bedingungen, damit wir Ihre Buchung vorläufig weiterfähren können.

Bedingungen akzeptieren:
{context['accept_url']}

Bedingungen ablehnen:
{context['reject_url']}

Wir freuen uns auf Ihre Rückmeldung und stehen bei Fragen jederzeit gerne zur Verfügung.

Mit freundlichen Grüßen
Ihr Kochstudio Team
""".strip()

        return body

    @staticmethod
    def build_price_lines(course, participant_count):
        """
        Build readable price lines for the selected course and group size.
        """

        if not course:
            return (
                "Die Preise richten sich nach dem gewählten Kochkurs und "
                "der finalen Teilnehmerzahl."
            )

        normalized_count = max(participant_count or 0, 1)

        categories = CoursePriceCategory.query.filter(
            CoursePriceCategory.cooking_course_id == course.id,
            CoursePriceCategory.active == 1,
            CoursePriceCategory.min_participants <= normalized_count,
            (
                (CoursePriceCategory.max_participants.is_(None)) |
                (CoursePriceCategory.max_participants >= normalized_count)
            )
        ).order_by(
            CoursePriceCategory.price_per_person.asc()
        ).all()

        if not categories:
            categories = CoursePriceCategory.query.filter_by(
                cooking_course_id=course.id,
                active=1
            ).order_by(
                CoursePriceCategory.min_participants.asc(),
                CoursePriceCategory.price_per_person.asc()
            ).all()

        if not categories:
            return (
                f"Für \"{course.name_de}\" sind aktuell noch keine "
                "Preiskategorien hinterlegt."
            )

        lines = [
            (
                f"Die Preise für \"{course.name_de}\" richten sich nach "
                "der gewählten Preiskategorie:"
            )
        ]

        for category in categories:
            discount_text = (
                f" - {category.discount_percent}% Gruppenrabatt"
                if category.discount_percent
                else ""
            )
            participant_range = EmailService.build_participant_range(category)
            description = (
                f"\n  {category.description_de}"
                if category.description_de
                else ""
            )
            lines.append(
                f"- {category.name_de} ({participant_range}): "
                f"{category.price_per_person} EUR pro Person"
                f"{discount_text}{description}"
            )

        return "\n".join(lines)

    @staticmethod
    def build_participant_range(category):
        """
        Build a readable participant range for a price category.
        """

        if category.max_participants:
            return (
                f"{category.min_participants}-{category.max_participants} "
                "Personen"
            )

        return f"ab {category.min_participants} Personen"

    @staticmethod
    def format_value(value, fallback):
        """
        Format date/time-like values for email text.
        """

        if not value:
            return fallback

        return str(value)

    @staticmethod
    def send_conditions_reminder(reservation):
        """
        Send a reminder to confirm reservation conditions.
        """

        condition = ReservationCondition.query.filter_by(
            reservation_id=reservation.id
        ).first()

        accept_url = url_for(
            "customer_workflow.accept_conditions_page",
            token=condition.confirmation_token,
            _external=True
        )

        subject = f"Erinnerung: Bedingungen {reservation.reservation_number}"

        body = (
            "Bitte bestätigen Sie die Bedingungen für Ihre vorläufige "
            f"Buchung.\n\nLink: {accept_url}"
        )

        return EmailService.send_email(
            reservation=reservation,
            email_type_code="conditions_reminder",
            recipient_email=reservation.customer.email,
            subject=subject,
            body=body
        )

    @staticmethod
    def get_offer_price_categories(reservation):
        """
        Return active price categories for the reservation course choices.

        When the participant count is known, only categories whose participant
        range matches the requested group size are returned.
        """

        course_ids = []

        for course_id in [
                reservation.first_choice_course_id,
                reservation.second_choice_course_id,
                reservation.cooking_course_id
        ]:
            if course_id and course_id not in course_ids:
                course_ids.append(course_id)

        if not course_ids:
            raise ValueError(
                "At least one cooking course is required before sending offers."
            )

        query = CoursePriceCategory.query.filter(
            CoursePriceCategory.active == 1,
            CoursePriceCategory.cooking_course_id.in_(course_ids)
        )

        participant_count = reservation.participant_count

        if participant_count:
            query = query.filter(
                CoursePriceCategory.min_participants <= participant_count,
                (
                    (CoursePriceCategory.max_participants.is_(None)) |
                    (CoursePriceCategory.max_participants >= participant_count)
                )
            )

        return query.order_by(
            CoursePriceCategory.cooking_course_id.asc(),
            CoursePriceCategory.min_participants.asc(),
            CoursePriceCategory.price_per_person.asc()
        ).all()

    @staticmethod
    def build_offer_category_line(category):
        """
        Build one readable offer line from a course price category.
        """

        course_name = (
            category.cooking_course.name_de
            if category.cooking_course
            else "Kochkurs"
        )
        participant_range = EmailService.build_participant_range(category)
        discount_text = (
            f", {category.discount_percent}% Gruppenrabatt"
            if category.discount_percent
            else ""
        )

        description = (
            f" - {category.description_de}"
            if category.description_de
            else ""
        )

        return (
            f"- {course_name}: {category.name_de} "
            f"({participant_range}) - "
            f"{category.price_per_person} EUR pro Person"
            f"{discount_text}{description}"
        )

    @staticmethod
    def send_offer_catalogue(reservation):
        """
        Send available course price categories to the customer.
        """

        condition = ReservationCondition.query.filter_by(
            reservation_id=reservation.id
        ).first()

        if not condition:
            raise ValueError(
                "ReservationCondition is required before sending offers."
            )

        offers = EmailService.get_offer_price_categories(reservation)

        if not offers:
            raise ValueError(
                "At least one active course price category is required."
            )

        offer_url = url_for(
            "customer_workflow.offer_selection_page",
            token=condition.confirmation_token,
            _external=True
        )

        offer_lines = [
            EmailService.build_offer_category_line(offer)
            for offer in offers
        ]

        subject = f"Angebote zu Ihrer Buchung {reservation.reservation_number}"

        body = (
            "Bitte wählen Sie Ihre Preiskategorie und ergänzen Sie Ihre "
            "Rechnungsadresse über das Formular.\n\n"
            + "\n".join(offer_lines)
            + f"\n\nFormular: {offer_url}"
        )

        return EmailService.send_email(
            reservation=reservation,
            email_type_code="offer_catalogue",
            recipient_email=reservation.customer.email,
            subject=subject,
            body=body
        )

    @staticmethod
    def send_offer_reminder(reservation):
        """
        Send a reminder to select a course price category.
        """

        condition = ReservationCondition.query.filter_by(
            reservation_id=reservation.id
        ).first()

        if not condition:
            raise ValueError(
                "ReservationCondition is required before sending offers."
            )

        offers = EmailService.get_offer_price_categories(reservation)

        if not offers:
            raise ValueError(
                "At least one active course price category is required."
            )

        offer_url = url_for(
            "customer_workflow.offer_selection_page",
            token=condition.confirmation_token,
            _external=True
        )

        subject = "Erinnerung: Angebotsauswahl erforderlich"

        body = (
            "Bitte wÃ¤hlen Sie Ihre Preiskategorie und geben Sie Ihre "
            f"Rechnungsadresse an.\n\nFormular: {offer_url}"
        )

        return EmailService.send_email(
            reservation=reservation,
            email_type_code="offer_reminder",
            recipient_email=reservation.customer.email,
            subject=subject,
            body=body
        )

    @staticmethod
    def send_reservation_confirmation(reservation):
        """
        Send final reservation confirmation.
        """

        subject = (
            f"Buchung endgültig reserviert "
            f"({reservation.reservation_number})"
        )

        body = (
            "Ihr Termin wurde endgültig reserviert. "
            "Wir freuen uns auf Ihr Event."
        )

        return EmailService.send_email(
            reservation=reservation,
            email_type_code="reservation_confirmed",
            recipient_email=reservation.customer.email,
            subject=subject,
            body=body
        )

    @staticmethod
    def send_manager_invoice_request(reservation):
        """
        Notify managers that an invoice should be created.
        """

        managers = Manager.query.all()

        for manager in managers:
            EmailService.send_email(
                reservation=reservation,
                email_type_code="manager_invoice_request",
                recipient_email=manager.email,
                subject="Rechnung erstellen",
                body=(
                    "Bitte erstellen Sie eine Rechnung für die Buchung. "
                    f"{reservation.reservation_number}."
                )
            )

    @staticmethod
    def send_calendar_invitations(reservation):
        """
        Send calendar invitations to collaborators.
        """

        collaborators = Collaborator.query.all()

        for collaborator in collaborators:
            EmailService.send_email(
                reservation=reservation,
                email_type_code="collaborator_invitation",
                recipient_email=collaborator.email,
                subject="Neue Kochstudio-Buchung",
                body=(
                    "Sie sind für die Buchung "
                    f"{reservation.reservation_number} eingeplant."
                )
            )