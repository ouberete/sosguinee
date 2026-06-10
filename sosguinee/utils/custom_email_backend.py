from django.core.mail.backends.smtp import EmailBackend
from smtplib import SMTP, SMTP_SSL
from django.conf import settings


class CustomEmailBackend(EmailBackend):
    def open(self):
        """Open a network connection with proper TLS/SSL and HELO.

        - Uses implicit SSL when EMAIL_USE_SSL is True (e.g., port 465).
        - Uses STARTTLS when EMAIL_USE_TLS is True.
        - Sends a valid local_hostname (HELO) using EMAIL_CLIENT_DOMAIN if provided.
        """
        if self.connection:
            return False
        try:
            local_hostname = getattr(settings, "EMAIL_CLIENT_DOMAIN", None) or "localhost"

            if getattr(self, "use_ssl", False):
                # Implicit SSL (e.g., Hostinger on port 465)
                self.connection = SMTP_SSL(
                    self.host,
                    self.port,
                    local_hostname=local_hostname,
<<<<<<< HEAD
=======
                    timeout=self.timeout,
>>>>>>> chore/security-design-hardening
                    context=self.ssl_context,
                )
            else:
                # Plain SMTP, optionally upgraded with STARTTLS
                self.connection = SMTP(
                    self.host,
                    self.port,
                    local_hostname=local_hostname,
<<<<<<< HEAD
=======
                    timeout=self.timeout,
>>>>>>> chore/security-design-hardening
                )
                if getattr(self, "use_tls", False):
                    self.connection.starttls(context=self.ssl_context)

            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except Exception:
            if not self.fail_silently:
                raise
            return False

