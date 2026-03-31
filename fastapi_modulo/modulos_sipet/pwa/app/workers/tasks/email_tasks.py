import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from app.workers.celery_app import celery_app
from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_message(
    to: str,
    subject: str,
    body_html: str,
    attachment_bytes: bytes | None = None,
    attachment_filename: str | None = None,
) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html"))

    if attachment_bytes and attachment_filename:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment_bytes)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{attachment_filename}"')
        msg.attach(part)

    return msg


@celery_app.task(bind=True, name="tasks.send_email", max_retries=3)
def send_email_task(
    self,
    to: str,
    subject: str,
    body_html: str,
    attachment_bytes: bytes | None = None,
    attachment_filename: str | None = None,
):
    if not settings.SMTP_HOST:
        logger.warning("SMTP not configured — email skipped")
        return {"status": "skipped"}

    try:
        msg = _build_message(to, subject, body_html, attachment_bytes, attachment_filename)
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, to, msg.as_string())
        logger.info("Email sent to %s", to)
        return {"status": "ok", "to": to}
    except Exception as exc:
        logger.error("Email failed to %s: %s", to, exc)
        raise self.retry(exc=exc, countdown=60)
