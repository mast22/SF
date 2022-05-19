import requests
from typing import Optional, Type
from dataclasses import dataclass
from django.conf import settings
from zeep import Client
from zeep.exceptions import TransportError
from lxml.etree import tostring
from requests import Response
from .. import logger
from . import exceptions as exc


@dataclass
class BaseSenderSettings:
    endpoint: str


class BaseSender:
    def __init__(self, settings: Type[BaseSenderSettings] or None=None):
        self.settings = settings

    def send_request(self, payload: dict, ocp_id: int or None=None):
        raise NotImplementedError()

    # def evaluate(self, service: BaseService):
    #     self.service = service
    #     self.service.process_before()
    #     try:
    #         response = self.send_request(self.service.get_payload())
    #     except Exception as err:
    #         # Проблемные запросы мы можем только логгировать
    #         logger.error(f'Получение ответа привело к {err} для {self.service.ocp.id}')
    #
    #         self.service.update_ocp_with_error()  # Обновляем статус OCP
    #
    #         raise FaultyRequestException()
    #
    #     self.service.process_response(response)

# class XMLSender(BaseSender):
#     def send_request(self, payload: dict):


@dataclass
class SoapSenderSettings(BaseSenderSettings):
    endpoint: tuple
    wsdl_file: str
    method: str


class SOAPSender(BaseSender):
    def __init__(self, settings: SoapSenderSettings or None=None):
        super().__init__()
        self.settings = settings

    def send_request(self, payload: dict, ocp_id: int or None=None):
        """
        Отправка soap запроса
        """
        wsdl_file = self.settings.wsdl_file
        method = self.settings.method
        endpoint = self.settings.endpoint

        xml_data = self.create_soap_xml(wsdl_file, method, payload, custom_endpoint=endpoint)
        logger.debug(f'XML to send {self.__class__}, ocp={ocp_id}: \n{xml_data}')

        result = self.send_soap_request(wsdl_file, method, payload, endpoint)
        logger.debug(f'Ответ для {wsdl_file} - {method} type:{type(result)})\n{result} ocp={ocp_id}')

        return result

    @staticmethod
    def create_soap_xml(wsdl_url, method_name, data, custom_endpoint: tuple or None=None) -> bytes:
        """Returns an xml file with soap request."""
        client = Client(wsdl_url)
        service = client.create_service(*custom_endpoint) if custom_endpoint else client.service
        soap_elem = client.create_message(service, method_name, **data)
        xml_data = tostring(soap_elem)
        return xml_data

    @staticmethod
    def send_soap_request(wsdl_url, method_name, data, custom_endpoint: tuple or None=None):
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
            raise exc.FaultyRequestException(f'Soap request error: {err.message}')
        return resp


class JSONSender(BaseSender):
    def send_request(self, payload: dict, ocp_id: int or None=None):
        endpoint = self.settings.endpoint
        ocp_id = self.settings.ocp.id
        try:
            result = requests.post(endpoint, payload).json()
            logger.debug(f'Ответ для {endpoint}: {result} ocp_id: {ocp_id}')
            return result
        except Exception as err:
            logger.error(f'Получение ответа привело к ошибке {err} для ocp_id: {ocp_id}')
            raise exc.FaultyRequestException()


class MockSender(BaseSender):
    """ Для тестирования """
    def __init__(self, settings: Type[BaseSenderSettings] or None=None):
        """ Добавляем список сервисов, которые мы вызвали в контексте провайдера """
        super(MockSender, self).__init__(settings)
        self.evaluated_ocps = {}

    def send_request(self, payload: dict, ocp_id: int or None=None):
        self.evaluated_ocps[ocp_id] = payload
        return Response()
