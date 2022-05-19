from django.test import TestCase

from apps.banks_app.otp.forms import CreateOptyBankForm, AddDocOpty
from ...const import BankBrand
from ..base_test_case import BaseBankFormMixin
from ..forms import CreateFormMixin


class CreateOptyTestCase(BaseBankFormMixin, CreateFormMixin, TestCase):
    bank_name = BankBrand.OTP
    bank_form = CreateOptyBankForm


class AddDocOptyTestCase(BaseBankFormMixin, TestCase):
    bank_form = AddDocOpty
    bank_name = BankBrand.OTP

    def test_compare_xml(self):
        self.form.set_documents([
            {
                'name': 'Паспорт',
                'type': 'Паспорт гражданина РФ',
                'ext': 'png',
                'buffer': 'ppDcHSAf2lwl7myoxAv5t/TtgyhJxi8p8i/hhOSGXcX1',
            }
        ])
        payload = self.form.convert_order_to_bank_payload()
        self.assertEqual(payload, {
            'Environment_Code': 'CRED_IT_TEST', 'TT_Ext_Code': '3632',
            'Agent_Ext_Code': '004451320751512813',
            'Chain_code': '008',
            'Opty_Id': str(self.order.id),
            'ListOfOpportunityAttachment': {
                'OpportunityAttachment': [
                    {'DocumentType': 'Паспорт гражданина РФ'},
                    {'OpptyFileName': 'Паспорт'},
                    {'OpptyFileExt': 'png'},
                    {'OpptyFileBuffer': 'ppDcHSAf2lwl7myoxAv5t/TtgyhJxi8p8i/hhOSGXcX1'},
                ]
            }
        })
