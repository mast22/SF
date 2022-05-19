from typing import Optional
from django.test import TestCase

from apps.orders.models import DocumentToSign
from ..base_test_case import BaseBankFormMixin
from ...const import CreditProductStatus, OrderStatus, BankBrand
from ...pochta.services import (
    CreateShortApplicationService,
    UpdateAttachmentService,
    SendToRTDMService,
    GetDocumentsService,
    ConfirmOfferService,
)

class ApplicationInfoMQResponseMock:
    """ Mock создаваемые в рантайме объекты zeep """
    def __init__(self, bank_id: str, ErrorCode: str='0',
                ErrorMessage: str='', Stage: str='Scoring', Status: str='Check Pending'):
        self.ApplicationIntId = bank_id
        self.ErrorCode = ErrorCode
        self.ErrorMessage = ErrorMessage
        self.Stage = Stage
        self.Status = Status


class ScoringServiceTestCase(BaseBankFormMixin, TestCase):
    bank_name = BankBrand.POCHTA
    bank_id = '1234'

    def setUp(self):
        super(ScoringServiceTestCase, self).setUp()
        self.service = CreateShortApplicationService(self.ocp)

        self.order.status = OrderStatus.SCORING # Статус устанавливается в workflow
        self.order.save()

    def test_process_response_valid(self):
        response = ApplicationInfoMQResponseMock(self.bank_id, '0', '', 'Scoring', 'Approved')

        self.service.process_before()
        self.ocp.refresh_from_db()
        self.assertEqual(self.ocp.status, CreditProductStatus.IN_PROCESS)

        self.service.process_response(response)

        self.order.refresh_from_db()
        self.ocp.refresh_from_db()

        self.assertEqual(self.bank_id, self.ocp.bank_id)
        # У нас есть положительный ответ от банка, поэтому выбор
        self.assertEqual(self.ocp.order.status, OrderStatus.SELECTION)
        self.assertEqual(self.ocp.status, CreditProductStatus.SUCCESS)

    def test_process_response_invalid(self):
        error_message = "Ошибка ошибка ошибка"
        response = ApplicationInfoMQResponseMock(self.bank_id, '1', error_message)

        self.service.process_response(response)

        self.order.refresh_from_db()
        self.ocp.refresh_from_db()

        self.assertEqual(self.bank_id, self.ocp.bank_id)
        self.assertEqual(self.ocp.order.status, OrderStatus.SCORING)
        self.assertEqual(self.ocp.status, CreditProductStatus.TECHNICAL_ERROR)
        self.assertEqual(self.ocp.bank_data, error_message)

    def test_process_response_rejected(self):
        response = ApplicationInfoMQResponseMock(self.bank_id, '0', '', 'Scoring', 'Cancelled')

        self.service.process_before()
        self.ocp.refresh_from_db()
        self.assertEqual(self.ocp.status, CreditProductStatus.IN_PROCESS)

        self.service.process_response(response)

        self.order.refresh_from_db()
        self.ocp.refresh_from_db()

        self.assertEqual(self.bank_id, self.ocp.bank_id)
        # У нас есть положительный ответ от банка, поэтому выбор
        self.assertEqual(self.ocp.order.status, OrderStatus.SELECTION)
        self.assertEqual(self.ocp.status, CreditProductStatus.REJECTED)



class UpdateAttachmentServiceTestCase(BaseBankFormMixin, TestCase):
    bank_name = BankBrand.POCHTA
    bank_id = '1234'

    def setUp(self):
        super(UpdateAttachmentServiceTestCase, self).setUp()
        self.service = UpdateAttachmentService(self.ocp)

    def test_process_response_valid(self):
        response = ApplicationInfoMQResponseMock(self.bank_id, '0', '', 'Scoring', 'Approved')

        self.service.process_before()
        self.ocp.refresh_from_db()
        self.assertEqual(self.ocp.status, CreditProductStatus.IN_PROCESS)

        self.service.process_response(response)

        self.order.refresh_from_db()
        self.ocp.refresh_from_db()

        self.assertEqual(self.bank_id, self.ocp.bank_id)
        self.assertEqual(self.ocp.order.status, OrderStatus.SELECTION)
        self.assertEqual(self.ocp.status, CreditProductStatus.SUCCESS)

    def test_process_response_invalid(self):
        error_message = "Ошибка Ошибка Ошибка"
        self.response = ApplicationInfoMQResponseMock("1", error_message)
        self.service.process_response(self.response)

        self.order.refresh_from_db()
        self.ocp.refresh_from_db()

        self.assertEqual(self.bank_id, self.ocp.bank_id)
        self.assertEqual(self.ocp.order.status, OrderStatus.SCORING)
        self.assertEqual(self.ocp.status, CreditProductStatus.TECHNICAL_ERROR)
        self.assertEqual(self.ocp.bank_data, error_message)


class SendToRTDMServiceTestCase(BaseBankFormMixin, TestCase):
    bank_name = BankBrand.POCHTA
    bank_id = '1234'

    def setUp(self):
        super(SendToRTDMServiceTestCase, self).setUp()
        self.service = SendToRTDMService(self.ocp)

        self.order.status = OrderStatus.SCORING # Статус устанавливается в workflow
        self.order.save()

    def test_process_response_valid(self):
        response = ApplicationInfoMQResponseMock(self.bank_id, '0', '', 'Scoring', 'Approved')

        self.service.process_before()
        self.ocp.refresh_from_db()
        self.assertEqual(self.ocp.status, CreditProductStatus.IN_PROCESS)

        self.service.process_response(response)

        self.order.refresh_from_db()
        self.ocp.refresh_from_db()

        self.assertEqual(self.bank_id, self.ocp.bank_id)
        # У нас есть положительный ответ от банка, поэтому выбор
        self.assertEqual(self.ocp.order.status, OrderStatus.SELECTION)
        self.assertEqual(self.ocp.status, CreditProductStatus.SUCCESS)

    def test_process_response_invalid(self):
        error_message = "Ошибка ошибка ошибка"
        response = ApplicationInfoMQResponseMock(self.bank_id, '1', error_message)

        self.service.process_response(response)

        self.order.refresh_from_db()
        self.ocp.refresh_from_db()

        self.assertEqual(self.bank_id, self.ocp.bank_id)
        self.assertEqual(self.ocp.order.status, OrderStatus.SCORING)
        self.assertEqual(self.ocp.status, CreditProductStatus.TECHNICAL_ERROR)
        self.assertEqual(self.ocp.bank_data, error_message)

    def test_process_response_rejected(self):
        response = ApplicationInfoMQResponseMock(self.bank_id, '0', '', 'Scoring', 'Cancelled')

        self.service.process_before()
        self.ocp.refresh_from_db()
        self.assertEqual(self.ocp.status, CreditProductStatus.IN_PROCESS)

        self.service.process_response(response)

        self.order.refresh_from_db()
        self.ocp.refresh_from_db()

        self.assertEqual(self.bank_id, self.ocp.bank_id)
        # У нас есть положительный ответ от банка, поэтому выбор
        self.assertEqual(self.ocp.order.status, OrderStatus.SELECTION)
        self.assertEqual(self.ocp.status, CreditProductStatus.REJECTED)



# Нужно получить полноценный ответ, чтобы было что тестить.
# class ConfirmOfferServiceTestCase(BaseBankFormMixin, TestCase):
#     bank_id = '3333'
#
#     def setUp(self):
#         super(ConfirmOfferServiceTestCase, self).setUp()
#
#         self.order.status = OrderStatus.AGREEMENT  # Начинаем принимать документы из этого статуса
#         self.order.save()
#         self.ocp.status = CreditProductStatus.SUCCESS
#         self.ocp.bank_id = self.bank_id
#         self.ocp.save()
#
#         self.service = ConfirmOfferService(self.ocp)
#
#     def test_process_response_valid(self):
#         request_doc_type = 'Заявление-анкета'
#         agreement_doc_type = 'Согласие на обработку данных'
#         response = CreateAgreementResponseMock(
#             Agreement_Number=self.bank_id,
#             MFO_Agreement_Flg='N',
#             Account_Number='1233',
#             Product_Code='12341',
#             Credit_Amount=33000.30,
#             First_Payment=10000,
#             Credit_Period=12,
#             PSK='30000',
#             Error_Code='0',
#             ListOfDocumentations=ListOfDocumentations([
#                 Document(
#                     Document_Type=request_doc_type,
#                     Document_Ext='pdf',
#                     Document_Buffer=b'LoremIpsumDolorSitAmet',
#                 ),
#                 Document(
#                     Document_Type=agreement_doc_type,
#                     Document_Ext='pdf',
#                     Document_Buffer=b'LoremIpsumDolorSitAmet123',
#                 ),
#             ]),
#             Error_Message=None
#         )
#         self.service.process_before()
#         self.order.refresh_from_db()
#
#         self.assertEqual(self.order.status, OrderStatus.DOCUMENTS_CREATION)
#         self.service.process_response(response)
#
#         self.ocp.refresh_from_db()
#         self.order.refresh_from_db()
#
#         self.assertEqual(self.order.status, OrderStatus.DOCUMENTS_SIGNING)
#         self.assertEqual(self.ocp.status, CreditProductStatus.SUCCESS)
#
#         self.assertTrue(DocumentToSign.objects.filter(
#             order=self.order,
#             file_name=request_doc_type,
#         ).exists())
#         self.assertTrue(DocumentToSign.objects.filter(
#             order=self.order,
#             file_name=agreement_doc_type,
#         ).exists())
#
#     def test_process_response_invalid(self):
#         error_message = 'ошибка ошибка'
#         response = CreateAgreementResponseMock(
#             Agreement_Number=self.bank_id,
#             MFO_Agreement_Flg='N',
#             Account_Number='1233',
#             Product_Code='12341',
#             Credit_Amount=33000.30,
#             First_Payment=10000,
#             Credit_Period=12,
#             PSK='30000',
#             Error_Code='1',
#             ListOfDocumentations=ListOfDocumentations([]),
#             Error_Message=error_message
#         )
#
#         self.service.process_before()
#         self.service.process_response(response)
#
#         self.ocp.refresh_from_db()
#         self.order.refresh_from_db()
#
#         # Статус заказа должен остаться подпись документов, но у OCP - тех ошибка
#         # Слишком сложная обработка ошибки, но она компенсируется практически невозможностью его прихода
#         self.assertEqual(self.ocp.status, CreditProductStatus.TECHNICAL_ERROR)
#         self.assertEqual(self.ocp.bank_data, error_message)
