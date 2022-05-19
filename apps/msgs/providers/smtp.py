from smtplib import SMTPException
from django.core.mail import get_connection, send_mail
from .base_provider import BaseProvider
from ..const import MessageSendResult, DEFAULT_REQUEST_TIMEOUT


class SmtpEmailProvider(BaseProvider):
    """Провайдер отправки почтовых сообщений через любой SMTP-сервер."""
    DEFAULT_SETTINGS = {
        'login': '',
        'password': '',
        'from': '',
        'host': '',
        'port': '',
        'as_html': False,
        'use_tls': False,
        'use_ssl': False,
        'timeout': DEFAULT_REQUEST_TIMEOUT,
        'ssl_keyfile': None,
        'ssl_certfile': None,
    }
    AUTH_CODE_METHODS = { 'EMAIL', }
    NOTIFICATION_METHODS = { 'EMAIL', }

    def send_email(self, to=None, receivers=None, text='', subject='', attachments=None, options=None):
        if to:
            receivers = (to,)
        as_html = options.get('as_html', self.settings['as_html'])
        try:
            connection = get_connection(
                fail_silently=False,
                host=options.get('host', self.settings['host']),
                port=options.get('port', self.settings['port']),
                username=options.get('login', self.settings['login']),
                password=options.get('password', self.settings['password']),
                use_tls=options.get('use_tls', self.settings['use_tls']),
                use_ssl=options.get('use_ssl', self.settings['use_ssl']),
                timeout=options.get('timeout', self.settings['timeout']),
                ssl_keyfile=options.get('ssl_keyfile', self.settings['ssl_keyfile']),
                ssl_certfile=options.get('ssl_certfile', self.settings['ssl_certfile'])
            )
            sent = send_mail(
                subject=subject,
                message=None if as_html else text,
                html_message=text if as_html else None,
                from_email=options.get('from', self.settings['from']),
                recipient_list=receivers,
                connection=connection
            )
        except SMTPException as err:
            result = MessageSendResult(False, None, 'smtp_exception', str(err))
        else:
            if sent:
                # There is no message id in current smtp-sending
                result = MessageSendResult(True, None, None, None, None)
            else:
                result = MessageSendResult(False, None, None, 'smtp_not_sent', 'SMTP Send error')
        return result
