from django.utils import timezone
from typing import Tuple, Type, Dict, Union
from .. import logger
from ..const import ServiceType
from . import exceptions as ex
from .forms import BaseBankForm
from .senders import BaseSender, SOAPSender, SoapSenderSettings
from apps.orders_ws.shortcuts import send_message_sync, WSMessageType
from apps.orders.const import CreditProductStatus
from apps.orders.models import OrderCreditProduct


class BaseService:
    """ Сервис банка

    Выполнение какой-либо задачи в банки сводится к вызову определенного сервиса
    Сервис - аналого workflow банка, но для OCP, т.е. изменение статусов заказа происходит при выполнении workflow
    также как и изменение статуса OCP происходит в Service, и обратное запрещено чтобы не нарушать процесс работы системы.

    Легче представить сервис, как обработка выполнения (как правило) SOAP запроса.
    """
    sender_class: Type[BaseSender] = SOAPSender
    form_class: Type[BaseBankForm]
    wsdl_file: str
    method: str
    # Засунем в endpoint 2 вариации: для json и xml. Жаль в питоне нет нормальных enum-ов
    endpoint: Union[Tuple[str, str], str, None]
    ocp: OrderCreditProduct

    def __init__(self, ocp: OrderCreditProduct, sender: Type[BaseSender] or None=None):
        self.ocp = ocp
        config = SoapSenderSettings(endpoint=self.endpoint, wsdl_file=self.wsdl_file, method=self.method)
        self.sender = sender(config) if sender else self.sender_class(config)

    def evaluate(self):
        """Обработка конкретного запроса"""
        self.process_before()
        response = self.process_request()
        return self.process_response(response)

    def update_ocp_with_error(self):
        text = f"Выполнение запроса закончилось с ошибкой. Обратитесь к разработчику OCP id = {self.ocp.id}" \
               f" {str(timezone.now())}"
        self.ocp.update_with_status(CreditProductStatus.TECHNICAL_ERROR, bank_data=text)

    def process_before(self):
        """ Выполняется в любом случае. Используется для управления состояния системы (OCP) """
        raise NotImplementedError()

    def process_response(self, data):
        """ Выполняет по факту прихода ответа от банка """
        raise NotImplementedError()

    def process_request(self):
        """Непосредственно запрос к api банка"""
        try:
            payload = self.get_payload()
            response = self.sender.send_request(payload, self.ocp.id)
        except Exception as err:
            # Проблемные запросы мы можем только логгировать
            logger.error(f'Получение ответа привело к ошибке: {err} для {self.ocp.id}')
            self.update_ocp_with_error()  # Обновляем статус OCP
            raise ex.FaultyRequestException()
        return response

    def get_payload(self) -> Dict:
        order = self.ocp.order
        credit_product = self.ocp.credit_product
        bank = credit_product.bank
        bank_form = self.form_class(ocp=self.ocp, order=order, bank=bank, credit_product=credit_product)
        return bank_form.convert_order_to_bank_payload()

