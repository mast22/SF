import os
import mimetypes
from typing import Callable
from io import BytesIO
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile

from apps.common import utils as u
from apps.common.models import one_to_one_get_or_new
from apps.common.transitions import change_state
from .. import logger
from . import forms
from apps.banks.const import ScoringResponse
from apps.orders.const import CreditProductStatus, OrderStatus
from apps.orders.models import OrderCreditProduct, DocumentToSign
from apps.orders_ws.shortcuts import send_message_sync, WSMessageType
from ..base.provider import BaseBankProvider
from . import const as c


class MTSBankProvider(BaseBankProvider):
    """Прослойка для работы с api МТС-банка."""



    def send_to_scoring(self):
        """ Отправка анкеты и документов на скоринг """
        # Отправляем анкету. мы отправляет как можно больше данных в одном запросе
        create_short_application_service = CreateShortApplicationService(self.ocp)
        result = create_short_application_service.evaluate()
        if not result:
            return result

        # Отправляем фотографии клиента
        update_attachment_service = UpdateAttachmentService(self.ocp)
        result = update_attachment_service.evaluate()
        if not result:
            return result

        # Отправляем заявку на проверку
        send_to_rtdm_service = SendToRTDMService(self.ocp)
        result = send_to_rtdm_service.evaluate()
        if not result:
            return result

        # Проверяем результат и запускаем задачу на периодическую проверку.
        return self.check_scoring_result()

    @staticmethod
    def process_client_refused_response(self, resp):
        """Обработка ответа на запрос об отказе клиента от заявки"""
        # Прямо сейчас вроде как ничего делать и не надо - статус меняем из вызывающего кода
        return True

    # ==== Скоринг. ====

    def send_to_scoring(self, *args, **kwargs):
        """Предварительная версия для логики отправки заявки на скоринг в Почта-Банк"""

        # 1. Отгружаем короткую заявку
        was_sent = self.scoring_send_short_form(*args, **kwargs)
        if not was_sent:
            return ScoringResponse(accepted=False, error_code=self.ocp.date_error_message)

        # 2. Загружаем сканы паспортных данных
        was_sent = self.scoring_upload_scans(*args, **kwargs)
        if not was_sent:
            return ScoringResponse(accepted=False, error_code=self.ocp.date_error_message)

        # 3. Просим отправить заявку на скоринг.
        was_sent = self.scoring_send_to_rtdm(*args, **kwargs)
        if not was_sent:
            return ScoringResponse(accepted=False, error_code=self.ocp.date_error_message)

        return ScoringResponse(accepted=True, error_code=self.ocp.date_error_message)
