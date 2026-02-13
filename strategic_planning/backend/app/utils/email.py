from typing import Optional
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


class EmailSender:
    """Clase para enviar emails usando SMTP."""

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD]):
            print("SMTP no configurado. Email no enviado.")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        msg["To"] = to_email

        if text_content:
            msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            return True
        except Exception as exc:
            print(f"Error enviando email: {exc}")
            return False


def send_verification_email(email_to: str, username: str, token: str) -> bool:
    subject = "Verifica tu email - Strategic Planning System"
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Verifica tu email</title>
    </head>
    <body>
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>¡Bienvenido a Strategic Planning System!</h2>
            <p>Hola {username},</p>
            <p>Gracias por registrarte. Para activar tu cuenta, por favor verifica tu email haciendo clic en el siguiente enlace:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{verification_url}"
                   style="background-color: #1890ff; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 4px; font-weight: bold;">
                    Verificar Email
                </a>
            </p>
            <p>O copia y pega este enlace en tu navegador:</p>
            <p style="background-color: #f5f5f5; padding: 10px; border-radius: 4px;">
                {verification_url}
            </p>
            <p>Este enlace expirará en 24 horas.</p>
            <p>Si no te registraste en nuestro sistema, por favor ignora este email.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                Strategic Planning System - Transformando la planificación estratégica
            </p>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    ¡Bienvenido a Strategic Planning System!

    Hola {username},

    Gracias por registrarte. Para activar tu cuenta, por favor verifica tu email visitando el siguiente enlace:

    {verification_url}

    Este enlace expirará en 24 horas.

    Si no te registraste en nuestro sistema, por favor ignora este email.

    Strategic Planning System - Transformando la planificación estratégica
    """

    return EmailSender.send_email(
        to_email=email_to,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
    )


def send_password_reset_email(email_to: str, username: str, token: str) -> bool:
    subject = "Restablece tu contraseña - Strategic Planning System"
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Restablecer contraseña</title>
    </head>
    <body>
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Restablecer contraseña</h2>
            <p>Hola {username},</p>
            <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta.</p>
            <p>Haz clic en el siguiente enlace para crear una nueva contraseña:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}"
                   style="background-color: #1890ff; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 4px; font-weight: bold;">
                    Restablecer Contraseña
                </a>
            </p>
            <p>O copia y pega este enlace en tu navegador:</p>
            <p style="background-color: #f5f5f5; padding: 10px; border-radius: 4px;">
                {reset_url}
            </p>
            <p>Este enlace expirará en 24 horas.</p>
            <p>Si no solicitaste restablecer tu contraseña, por favor ignora este email.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                Strategic Planning System - Transformando la planificación estratégica
            </p>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Restablecer contraseña

    Hola {username},

    Recibimos una solicitud para restablecer la contraseña de tu cuenta.

    Visita el siguiente enlace para crear una nueva contraseña:

    {reset_url}

    Este enlace expirará en 24 horas.

    Si no solicitaste restablecer tu contraseña, por favor ignora este email.

    Strategic Planning System - Transformando la planificación estratégica
    """

    return EmailSender.send_email(
        to_email=email_to,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
    )
