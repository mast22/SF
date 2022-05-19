from typing import Optional, List

from django.test import TestCase

from apps.orders.models import DocumentToSign
from ..base_test_case import BaseBankFormMixin
from ...otp.services.create_agreement import CreateAgreementService
from ...otp.services.scoring import ScoringService
from ...otp.services.client_refused import ClientRefusedService
from ...const import CreditProductStatus, OrderStatus


class CreateOptyResponseMock:
    """ Mock создаваемые в рантайме объекты zeep """

    def __init__(self, Opty_Id: str, Error_Code: str, Error_Message: Optional[str]):
        self.Opty_Id = Opty_Id
        self.Error_Code = Error_Code
        self.Error_Message = Error_Message


class ScoringServiceTestCase(BaseBankFormMixin, TestCase):
    bank_id = '3333'

    def setUp(self):
        super(ScoringServiceTestCase, self).setUp()
        self.service = ScoringService(self.ocp)

        self.order.status = OrderStatus.SCORING # Статус устанавливается в workflow
        self.order.save()

    def test_process_response_valid(self):
        self.response = CreateOptyResponseMock(self.bank_id, "0", None)

        self.service.process_before()
        self.ocp.refresh_from_db()
        self.assertEqual(self.ocp.status, CreditProductStatus.IN_PROCESS)

        self.service.process_response(self.response)

        self.order.refresh_from_db()
        self.ocp.refresh_from_db()

        self.assertEqual(self.ocp.bank_id, self.bank_id)
        # У нас есть положительный ответ от банка, поэтому выбор
        self.assertEqual(self.ocp.order.status, OrderStatus.SELECTION)
        self.assertEqual(self.ocp.status, CreditProductStatus.SUCCESS)

    def test_process_response_invalid(self):
        error_message = "Ошибка ошибка ошибка"
        self.response = CreateOptyResponseMock(self.bank_id, "1", error_message)

        self.service.process_response(self.response)

        self.order.refresh_from_db()
        self.ocp.refresh_from_db()

        self.assertEqual(self.ocp.bank_id, self.bank_id)
        self.assertEqual(self.ocp.order.status, OrderStatus.SCORING)
        self.assertEqual(self.ocp.status, CreditProductStatus.TECHNICAL_ERROR)
        self.assertEqual(self.ocp.bank_data, error_message)


class RejectOptyResponseMock:
    def __init__(self, Error_Code: str, Error_Message: Optional[str]):
        """ Mock ответа на запрос отказа клиента """
        self.Error_Code = Error_Code
        self.Error_Message = Error_Message


class ClientRefusedServiceTestCase(BaseBankFormMixin, TestCase):
    def setUp(self):
        super(ClientRefusedServiceTestCase, self).setUp()
        self.service = ClientRefusedService(self.ocp)

    def test_process_response_valid(self):
        self.response = RejectOptyResponseMock("0", None)

        self.service.process_response(self.response)

    def test_process_response_invalid(self):
        error_message = "Ошибка Ошибка Ошибка"
        self.response = RejectOptyResponseMock("1", error_message)
        self.service.process_response(self.response)

        self.assertEqual(self.ocp.bank_data, error_message)
        self.assertEqual(self.ocp.status, CreditProductStatus.TECHNICAL_ERROR)

    def test_process_service(self):
        self.service.process_before()

        self.assertEqual(self.ocp.status, CreditProductStatus.CLIENT_REFUSED)


class Document:
    def __init__(self, Document_Type: str, Document_Ext: str, Document_Buffer: bytes):
        self.Document_Type = Document_Type
        self.Document_Ext = Document_Ext
        self.Document_Buffer = Document_Buffer


class ListOfDocumentations:
    def __init__(self, Document: List[Document]):
        self.Document = Document


class CreateAgreementResponseMock:
    def __init__(
            self,
            Agreement_Number: str,
            MFO_Agreement_Flg: str,
            Account_Number: str,
            Product_Code: str,
            Credit_Amount: float,
            First_Payment: int,
            Credit_Period: int,
            PSK: str,
            Error_Code: str,
            ListOfDocumentations: ListOfDocumentations,
            Error_Message: Optional[str],
    ):
        self.Agreement_Number = Agreement_Number
        self.MFO_Agreement_Flg = MFO_Agreement_Flg
        self.Account_Number = Account_Number
        self.Product_Code = Product_Code
        self.Credit_Amount = Credit_Amount
        self.First_Payment = First_Payment
        self.Credit_Period = Credit_Period
        self.PSK = PSK
        self.Error_Code = Error_Code
        self.ListOfDocumentations = ListOfDocumentations
        self.Error_Message = Error_Message


class CreateAgreementServiceTestCase(BaseBankFormMixin, TestCase):
    bank_id = '3333'

    def setUp(self):
        super(CreateAgreementServiceTestCase, self).setUp()

        self.order.status = OrderStatus.AGREEMENT  # Начинаем принимать документы из этого статуса
        self.order.save()
        self.ocp.status = CreditProductStatus.SUCCESS
        self.ocp.bank_id = self.bank_id
        self.ocp.save()

        self.service = CreateAgreementService(self.ocp)

    def test_process_response_valid(self):
        request_doc_type = 'Заявление-анкета'
        agreement_doc_type = 'Согласие на обработку данных'
        response = CreateAgreementResponseMock(
            Agreement_Number=self.bank_id,
            MFO_Agreement_Flg='N',
            Account_Number='1233',
            Product_Code='12341',
            Credit_Amount=33000.30,
            First_Payment=10000,
            Credit_Period=12,
            PSK='30000',
            Error_Code='0',
            ListOfDocumentations=ListOfDocumentations([
                Document(
                    Document_Type=request_doc_type,
                    Document_Ext='pdf',
                    Document_Buffer=b'LoremIpsumDolorSitAmet',
                ),
                Document(
                    Document_Type=agreement_doc_type,
                    Document_Ext='pdf',
                    Document_Buffer=b'LoremIpsumDolorSitAmet123',
                ),
            ]),
            Error_Message=None
        )
        self.service.process_before()
        self.order.refresh_from_db()

        self.assertEqual(self.order.status, OrderStatus.DOCUMENTS_CREATION)
        self.service.process_response(response)

        self.ocp.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(self.order.status, OrderStatus.DOCUMENTS_SIGNING)
        self.assertEqual(self.ocp.status, CreditProductStatus.SUCCESS)

        self.assertTrue(DocumentToSign.objects.filter(
            order=self.order,
            file_name=request_doc_type,
        ).exists())
        self.assertTrue(DocumentToSign.objects.filter(
            order=self.order,
            file_name=agreement_doc_type,
        ).exists())

    def test_process_response_invalid(self):
        error_message = 'ошибка ошибка'
        response = CreateAgreementResponseMock(
            Agreement_Number=self.bank_id,
            MFO_Agreement_Flg='N',
            Account_Number='1233',
            Product_Code='12341',
            Credit_Amount=33000.30,
            First_Payment=10000,
            Credit_Period=12,
            PSK='30000',
            Error_Code='1',
            ListOfDocumentations=ListOfDocumentations([]),
            Error_Message=error_message
        )

        self.service.process_before()
        self.service.process_response(response)

        self.ocp.refresh_from_db()
        self.order.refresh_from_db()

        # Статус заказа должен остаться подпись документов, но у OCP - тех ошибка
        # Слишком сложная обработка ошибки, но она компенсируется практически невозможностью его прихода
        self.assertEqual(self.ocp.status, CreditProductStatus.TECHNICAL_ERROR)
        self.assertEqual(self.ocp.bank_data, error_message)
