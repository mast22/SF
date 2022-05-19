from unittest import TestCase

from apps.banks_app.otp.provider import OTPBankProvider
from apps.banks_app.base.senders import MockSender
from apps.banks_app.otp.services.client_refused import ClientRefusedService
from apps.banks_app.otp.services.create_agreement import CreateAgreementService
from apps.banks_app.otp.services.send_authorization import SendAuthorizationService
from apps.banks_app.otp.services.send_documents import SendDocumentsService
from apps.banks.models import Bank
from apps.common.utils import instance_of_in
from apps.orders.models import OrderCreditProduct, Order


class OtpProviderTestCase(TestCase):
    """ Мои первые шаги в тестирование бизнес логики без запросов к БД
    Некоторые из данных
    """

    def setUp(self) -> None:
        ocp = OrderCreditProduct()
        bank = Bank()
        order = Order()
        self.provider = OTPBankProvider(ocp=ocp, order=order, bank=bank, sender=MockSender)

    def tearDown(self) -> None:
        self.provider.sender.evaluated_services = []

    def test_send_to_scoring(self):
        """ Невозможно протестить пока там выполняется WS запрос """

    def test_send_client_refused(self):
        self.provider.send_client_refused()
        self.assertTrue(instance_of_in(ClientRefusedService, self.provider.sender.evaluated_services))

    def test_send_agreement(self):
        self.provider.send_agreement()
        self.assertTrue(instance_of_in(CreateAgreementService, self.provider.sender.evaluated_services))

    def test_send_documents(self):
        self.provider.send_documents()
        self.assertTrue(instance_of_in(SendDocumentsService, self.provider.sender.evaluated_services))
        self.assertTrue(instance_of_in(SendAuthorizationService, self.provider.sender.evaluated_services))

    def test_send_authorization(self):
        self.provider.send_authorization()
        self.assertTrue(instance_of_in(SendAuthorizationService, self.provider.sender.evaluated_services))
