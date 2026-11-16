from email.message import EmailMessage
from typing import Protocol
from urllib.parse import urlencode
import smtplib

from app.core.config import Settings
from app.core.exceptions import ServiceUnavailableError


class EmailSender(Protocol):
    @property
    def is_configured(self) -> bool: ...

    def send_verification(self, email: str, token: str) -> None: ...

    def send_password_reset(self, email: str, token: str) -> None: ...


class SMTPEmailService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return all(
            (
                self.settings.smtp_host,
                self.settings.email_from,
                self.settings.frontend_base_url,
            )
        )

    def send_verification(self, email: str, token: str) -> None:
        link = self._frontend_link("/auth/verify-email", token)
        self._send(email, "Verify your T2S account", f"Verify your email address: {link}")

    def send_password_reset(self, email: str, token: str) -> None:
        link = self._frontend_link("/auth/reset-password", token)
        self._send(email, "Reset your T2S password", f"Reset your password: {link}")

    def _frontend_link(self, path: str, token: str) -> str:
        if not self.is_configured:
            raise ServiceUnavailableError("Email delivery is not configured.")
        return (
            f"{self.settings.frontend_base_url.rstrip('/')}{path}?"
            f"{urlencode({'token': token})}"
        )

    def _send(self, recipient: str, subject: str, body: str) -> None:
        if not self.is_configured:
            raise ServiceUnavailableError("Email delivery is not configured.")
        if self.settings.is_production and not (
            self.settings.smtp_starttls or self.settings.smtp_use_ssl
        ):
            raise ServiceUnavailableError("Secure SMTP transport is required in production.")
        message = EmailMessage()
        message["From"] = self.settings.email_from
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        try:
            smtp_client = smtplib.SMTP_SSL if self.settings.smtp_use_ssl else smtplib.SMTP
            with smtp_client(self.settings.smtp_host, self.settings.smtp_port, timeout=10) as smtp:
                if self.settings.smtp_starttls and not self.settings.smtp_use_ssl:
                    smtp.starttls()
                if self.settings.smtp_user:
                    password = self.settings.smtp_password
                    smtp.login(
                        self.settings.smtp_user,
                        password.get_secret_value() if password else "",
                    )
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException):
            raise ServiceUnavailableError("Email delivery is unavailable.") from None
