from django.core.mail.backends.smtp import EmailBackend
from ntlm.smtp import ntlm_authenticate
import smtplib
from django.core.mail.utils import DNS_NAME

class NTLMEmail(EmailBackend):
    def open(self):
        """
        Ensures we have a connection to the email server. Returns whether or
        not a new connection was required (True or False).
        """
        if self.connection:
            # Nothing to do if the connection is already open.
            return False
        try:
            # If local_hostname is not specified, socket.getfqdn() gets used.
            # For performance, we use the cached FQDN for local_hostname.
            self.connection = smtplib.SMTP(self.host, self.port,
                                           local_hostname=DNS_NAME.get_fqdn())
            self.connection.ehlo()
            if self.username and self.password:
                ntlm_authenticate(self.connection, self.username, self.password)
            return True
        except:
            if not self.fail_silently:
                raise
