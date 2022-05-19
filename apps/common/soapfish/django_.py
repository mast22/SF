from .core import SOAPRequest
from .soap_dispatch import SOAPDispatcher
from apps.banks import logger

__all__ = ['django_dispatcher']


class DjangoEnvironWrapper:
    def __init__(self, environ):
        self.environ = environ

    def get(self, name, default=None):
        name = name.replace('-', '_').upper()
        for key in (name, 'HTTP_' + name):
            if key in self.environ:
                return self.environ[key]
        return default


def django_dispatcher(service, **dispatcher_kwargs):
    from django.http import HttpResponse
    from django.views.decorators.csrf import csrf_exempt

    def django_dispatch(request):
        dispatcher_kwargs_local = {**dispatcher_kwargs}
        resend_to = dispatcher_kwargs_local.pop('resend_to', None)
        if resend_to:
            logger.debug(f'Resend to {resend_to} data: {request.body}')
            resend_soap_request(resend_to, request.body)
        else:
            logger.debug(f'Do not need to resend data, service: {service}!')

        soap_request = SOAPRequest(DjangoEnvironWrapper(request.environ), request.body)
        soap_request._original_request = request
        soap_dispatcher = SOAPDispatcher(service, **dispatcher_kwargs_local)
        soap_response = soap_dispatcher.dispatch(soap_request)

        response = HttpResponse(soap_response.http_content)
        response.status_code = soap_response.http_status_code
        for k, v in soap_response.http_headers.items():
            response[k] = v

        return response

    return csrf_exempt(django_dispatch)


def resend_soap_request(url, data):
    import requests
    requests.post(url, data=data, timeout=5, verify=False)

