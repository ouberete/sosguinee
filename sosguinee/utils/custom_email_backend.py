# utils/custom_email_backend.py
from django.core.mail.backends.smtp import EmailBackend
from smtplib import SMTP

class CustomEmailBackend(EmailBackend):
    def open(self):
        """Override to fix Invalid domain name (HELO)"""
        if self.connection:
            return False
        try:
            self.connection = SMTP(
                self.host,
                self.port,
                local_hostname="sosguinee.org"  # <- Forcer un nom d’hôte valide ici
            )
            if self.use_tls:
                self.connection.starttls(context=self.ssl_context)
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except Exception:
            if not self.fail_silently:
                raise
            return False
