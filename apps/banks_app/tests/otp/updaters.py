import copy
import uuid
from typing import Dict

from django.test import TestCase
from django.urls import reverse

from ...const import BankBrand, OrderStatus, CreditProductStatus
from ..base_test_case import BaseBankFormMixin
from apps.banks.utils import create_soap_xml


class ReceiveCreditDecisionTestCase(BaseBankFormMixin, TestCase):
    bank_name = BankBrand.OTP
    bank_id = str(uuid.uuid4())
    sample_payload = dict(
        environmentCode='CRED_IT_TEST',
        reference=bank_id,
        decision=1,
        product='PKP239_M8_24',
        amount=95000.0,
        downPayment=25000.0,
        creditTerm=24.0,
        referenceKB=None,
        source='OTPBank',
        monthlypaymentamount=None,
        requestForm=None,
        requestFormComment=None,
        CreditAmount=None,
        FullAgentServicesAmount=None,
        AgentServicesAmount=None,
        limitCartOfGoods=None,
        SMSBankAmount=None,
        NeedNoConsent='N',
    )

    def setUp(self):
        super(ReceiveCreditDecisionTestCase, self).setUp()
        self.order.status = OrderStatus.SCORING
        self.order.save()
        self.ocp.bank_id = self.bank_id
        self.ocp.save()

    def make_request(self, data: Dict):
        wsdl_file = 'apps/banks_app/wsdl/otp/broker-receive-credit-decision-api.wsdl'
        otp_data_xml = create_soap_xml(
            wsdl_file, 'receiveCreditDecision', data,
            ('{http://siebel.com/CustomUI}CreditDecisionPort', '127.0.0.1')
        )

        receive_credit_decision_url = reverse('api:soap:otp:receive-credit-decision')
        resp = self.client.post(receive_credit_decision_url, otp_data_xml, content_type='text/xml')
        self.assertEqual(resp.status_code, 200)

        return resp

    def test_send_successful_decision(self):
        # Файл для примера отправим без изменения
        self.make_request(self.sample_payload)

        self.ocp.refresh_from_db()
        self.assertEqual(
            self.ocp.status,
            CreditProductStatus.SUCCESS,
        )

    def test_send_unsuccessful_decision(self):
        unsuccessful_payload = copy.copy(self.sample_payload)
        unsuccessful_payload['decision'] = 0

        self.make_request(unsuccessful_payload)

        self.ocp.refresh_from_db()
        self.assertEqual(
            self.ocp.status,
            CreditProductStatus.REJECTED,
        )

# TODO Не доделали функционал, нет тестов
class ControlResultAgreement(BaseBankFormMixin, TestCase):
    bank_id = str(uuid.uuid4())
    sample_payload = dict(
        EnvironmentCode='CRED_IT_TEST',
        OptyID=bank_id,
        comment='',
        CheckResult=1,
        OpportunityAttachments={
            'OpportunityAttachment': [
                {
                    'DocumentType': 'Паспорт гражданина РФ',
                    'OptyFileName': 'паспорт.jpg',
                    'OptyFileStatus': 'N',
                    'OptyFileComment': 'Плохая фотография',
                },
            ]
        }
    )

    def setUp(self):
        super(ControlResultAgreement, self).setUp()
        self.ocp.bank_id = self.bank_id
        self.ocp.save()

    def make_request(self, data: Dict):
        wsdl_file = 'apps/banks_app/wsdl/otp/broker-control-result-agreement-api.wsdl'
        otp_data_xml = create_soap_xml(
            wsdl_file, 'receiveCreditDecision', data,
            ('{http://siebel.com/CustomUI}CreditDecisionPort', '127.0.0.1')
        )

        receive_credit_decision_url = reverse('api:soap:otp:receive-credit-decision')
        resp = self.client.post(receive_credit_decision_url, otp_data_xml, content_type='text/xml')
        self.assertEqual(resp.status_code, 200)

        return resp

