from django.conf import settings
from zeep import Client
from zeep.exceptions import TransportError
from lxml.etree import tostring
from . import logger


def create_soap_xml(wsdl_url, method_name, data, custom_endpoint: tuple or None = None) -> bytes:
    """Returns an xml file with soap request."""
    client = Client(wsdl_url)
    service = client.create_service(*custom_endpoint) if custom_endpoint else client.service
    soap_elem = client.create_message(service, method_name, **data)
    xml_data = tostring(soap_elem)
    return xml_data


def send_soap_request(wsdl_url, method_name, data, custom_endpoint: tuple or None = None):
    """Generate soap request based on wsdl file.
    :param str wsdl_url: url or local path to wsdl file
    :param str method_name: Name of Soap Message sending method
    :param dict data: Data to send in soap request
    :param tuple or None custom_endpoint: tuple of 2 elements: binding_name, address
        could be something like: ('{http://siebel.com/CustomUI}CreditDecisionPort', 'http://localhost/api/soap/')
    :return:
        response from soap server.
    """
    client = Client(wsdl_url)
    client.transport.session.verify = settings.VERIFY_SSL

    service = client.create_service(*custom_endpoint) if custom_endpoint else client.service
    try:
        resp = service[method_name](**data)
    except TransportError as err:
        logger.error('Soap request error' + f'{err.message}')
        resp = None
    return resp

    # soap_proxy = client.create_message(service, method_name, **data)
    # return soap_proxy
