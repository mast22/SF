import os
import mimetypes
from typing import Callable
from io import BytesIO
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile

from apps.common import utils as u
from apps.common.models import one_to_one_get_or_new
from apps.common.transitions import change_state
from apps.banks import logger
from . import forms
from apps.banks.const import ScoringResponse
from apps.orders.const import CreditProductStatus, OrderStatus
from apps.orders.models import OrderCreditProduct, DocumentToSign
from apps.orders_ws.shortcuts import send_message_sync, WSMessageType
from ..base.provider import BaseBankProvider
from . import const as c
from apps.banks.tasks import scoring_check_result_task


class PochtaBankProvider(BaseBankProvider):
    """Прослойка для работы с api почта-банка."""

    def scoring_send_short_form(self):
        """Отправка на скоринг короткой заявки"""
        resp = self.process_soap_request(
            self.REQUESTS_SETTINGS['scoring'],
            on_response_callback=self.process_scoring_short_form_response
        )
        return resp is not None

    @staticmethod
    def process_scoring_short_form_response(self, resp):
        """Обработка ответа после создания короткой формы"""
        self.ocp.bank_id = resp.ApplicationIntId
        self.ocp.save(update_fields=('bank_id',))
        return True

    def scoring_upload_scans(self):
        """Загрузка сканов паспорта в заявку"""
        resp = self.process_soap_request(
            self.REQUESTS_SETTINGS['update_attachment'],
            on_response_callback=self.process_scoring_update_attachment_response
        )
        return resp is not None

    def process_scoring_update_attachment_response(self, resp):
        """Обработка ответа о загрузке паспортных данных"""
        # В заявке менять ничего не нужно.
        return True

    def scoring_send_to_rtdm(self):
        """Отправка загруженной заявки на скоринг"""
        resp = self.process_soap_request(
            self.REQUESTS_SETTINGS['rtdm'],
            on_response_callback=self.process_scoring_send_to_rtdm_response
        )
        return resp is not None

    def send_to_scoring(self):
        """Предварительная версия для логики отправки заявки на скоринг в Почта-Банк"""

        # 1. Отгружаем короткую заявку
        was_sent = self.scoring_send_short_form()
        if not was_sent:
            return ScoringResponse(accepted=False, error_code=self.ocp.date_error_message)

        # 2. Загружаем сканы паспортных данных
        was_sent = self.scoring_upload_scans()
        if not was_sent:
            return ScoringResponse(accepted=False, error_code=self.ocp.date_error_message)

        # 3. Просим отправить заявку на скоринг.
        was_sent = self.scoring_send_to_rtdm()
        if not was_sent:
            return ScoringResponse(accepted=False, error_code=self.ocp.date_error_message)

        # Теперь нужно запустить цикл для ожидания результата скоринга.
        # TODO: Написать логику, которая подойдёт и для dramatiq и для синхронного ожидания в цикле.
        # Запускаем dramatiq-таск, который будет ждать результат скоринга.
        scoring_check_result_task.apply(self.ocp.id)

        return ScoringResponse(accepted=True, error_code=self.ocp.date_error_message)

    def process_scoring_send_to_rtdm_response(self, resp):
        """Обработка ответа о запросе на скоринг"""
        # В заявке менять ничего не нужно
        return True

    def scoring_check_result(self):
        resp = self.process_soap_request(self.REQUESTS_SETTINGS['scoring-check-result'],
                                         on_response_callback=self.process_scoring_check_result_response)
        return resp is not None

    def process_scoring_check_result_response(self, resp):
        """Обработка ответа на запрос результата скоринга"""
        # Сохранить в ocp результат скоринга, если статус заказа в банке = проскорено.
        try:
            decision = c.POCHTA_CREDIT_DECISIONS[int(resp.DecisionCode)]
            logger.info(f'{self.bank.name} response: {resp} for request: order: {self.ocp.order}, ocp: {self.ocp}')
            self.ocp.update_with_status(decision)
            return ScoringResponse(accepted=True, error_code=None, error_details=None, bank_id=self.ocp.bank_id)
        except Exception as err:
            logger.error(err)
            return ScoringResponse(accepted=False, error_code=1, error_details=str(err), bank_id=self.ocp.bank_id)

    # ==== Работа с заявкой после скоринга. ====

    def send_client_approve_ci(self):
        """Отправка подтверждения клиента на запрос во внешний БКИ"""
        return self.process_soap_request(self.REQUESTS_SETTINGS['client_approve_ci'])

    def process_client_approve_ci_response(self, resp):
        """Обработка ответа на отправку согласия клиента на доп. проверку через БКИ"""
        return True

    def send_agreement(self):
        """Отправка согласия клиента на данный кредитный продукт в Почта-банк"""
        was_confirmed = self.process_soap_request(self.REQUESTS_SETTINGS['confirm_offer'],
                                                  on_response_callback=self.process_confirm_offer_response)
        if was_confirmed:
            resp = self.process_soap_request(self.REQUESTS_SETTINGS['get_documents'],
                                             on_response_callback=self.process_confirm_offer_response)
        else:
            resp = False
        return resp

    def process_confirm_offer_response(self, resp):
        """Обработка ответа на отправку согласия клиента на получение кредита"""
        # TODO: Дописать логику (по идее - только проверить, что нет ошибок, что уже сделано на момент попадания сюда)
        return True

    def get_documents(self, resp):
        """Обработка ответа на получение печатных форм для подписания клиентом"""
        doc_ids = []
        if resp.CheckResult == c.DocumentsCheckResult.APPROVED:
            # Печатные формы сгенерированы.
            for app_pos in resp.ListOfBrokerApplicationPf:
                for document in app_pos.ListOfOpportunityPf:
                    # TODO: Протестить логику
                    # document.OpptyFileNamePF
                    # document.OpptyFileSrcType
                    # document.OpptyFileBuffer

                    doc_type = document.OpptyFileNamePF
                    doc_name, doc_ext = os.path.splitext(document.OpptyFileNamePF)  # TODO - может и не так всё!
                    doc_ext = doc_ext.lower() if doc_ext else 'txt'
                    doc_mimetype = mimetypes.types_map.get('.' + doc_ext, 'text/plain')
                    doc_name = f'order_{self.order.id}_document_{u.generate_random_uuid()}_{doc_name}.{doc_ext}'
                    doc_file_bytes = document.OpptyFileBuffer
                    doc_file = InMemoryUploadedFile(
                        file=BytesIO(doc_file_bytes), field_name='file',
                        name=doc_name, content_type=doc_mimetype,
                        size=len(doc_file_bytes), charset='utf-8'
                    )
                    doc = DocumentToSign.objects.create(
                        order=self.order, file=doc_file,
                        file_name=doc_type, file_ext=doc_ext
                    )
                    doc_ids.append(doc.id)

        # Отправить по ws уведомление агенту, что печатные формы сохранены.
        send_message_sync(self.order.agent_id, self.order.id,
                          type=WSMessageType.DOCUMENTS_TO_SIGN, data={'documents': doc_ids, })

        return True

    def send_documents(self):
        """Отправка подписанных клиентом документов в Почта-банк"""
        return self.process_soap_request(self.REQUESTS_SETTINGS['docs_signed'])

    @staticmethod
    def process_add_documents_response(self, resp, credit_product, resp_conf):
        """Обработка ответа на отправку подписанных документов
        AddDocOpty
        """
        # TODO: Дописать логику
        return True

    def send_authorization(self):
        """Отправка окончательного подвтерждения от клиента о взятии кредита в Почта-банке"""
        return self.process_soap_request(self.REQUESTS_SETTINGS['check_status'])

    def process_authorize_agreement_response(self, resp, credit_product, resp_conf):
        """Обработка ответа на подтверждения согласия клиента после отправки подписанных документов
        AuthorizeAgreement
        """
        change_state(self.order.set_authorized, 'Inner Error on setting AUTHORIZED status')
        self.order.save()
        one_to_one_get_or_new(self.order, 'contract', creation_kwargs={})
        return True
