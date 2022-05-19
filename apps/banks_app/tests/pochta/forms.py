import logging

from django.test import TestCase

from ...pochta.forms import CreateShortApplicationMQBankForm, UpdateAttachmentMQBankForm, \
    SendToRTDMMQForm, GetDocsForm, DocsSignedForm, CheckStatusForm, ConfirmOfferForm
from ...pochta.services import CreateShortApplicationService, UpdateAttachmentService, SendToRTDMService, \
    GetDocumentsService, ConfirmOfferService
from ...const import BankBrand
from ..base_test_case import BaseBankFormMixin
from ..forms import CreateFormMixin, BaseFormConversionMixin

logger = logging.getLogger('testing')


class CreateShortApplicationMQBankFormTestCase(CreateFormMixin, BaseBankFormMixin, TestCase):
    """ Форма с данными клиента """
    bank_name = BankBrand.POCHTA
    bank_form = CreateShortApplicationMQBankForm
    service = CreateShortApplicationService


class UpdateAttachmentMQBankFormTestCase(BaseFormConversionMixin, BaseBankFormMixin, TestCase):
    """ Форма с документами клиента """
    bank_name = BankBrand.POCHTA
    bank_form = UpdateAttachmentMQBankForm
    service = UpdateAttachmentService


class SendToRTDMMQBankFormTestCase(BaseFormConversionMixin, BaseBankFormMixin, TestCase):
    bank_name = BankBrand.POCHTA
    bank_form = SendToRTDMMQForm
    service = SendToRTDMService


class GetDocsFormTestCase(BaseFormConversionMixin, BaseBankFormMixin, TestCase):
    bank_name = BankBrand.POCHTA
    bank_form = GetDocsForm
    service = GetDocumentsService

    def setUp(self):
        super(GetDocsFormTestCase, self).setUp()
        self.ocp.bank_id = '3333'
        self.ocp.save()


class DocsSignedFormTestCase(BaseFormConversionMixin, BaseBankFormMixin, TestCase):
    bank_name = BankBrand.POCHTA
    bank_form = DocsSignedForm
    # service = DocsSignedService


class CheckStatusFormTestCase(BaseFormConversionMixin, BaseBankFormMixin, TestCase):
    bank_name = BankBrand.POCHTA
    bank_form = CheckStatusForm
    # service = CheckStatusService


class ConfirmOfferFormTestCase(BaseFormConversionMixin, BaseBankFormMixin, TestCase):
    bank_name = BankBrand.POCHTA
    bank_form = ConfirmOfferForm
    service = ConfirmOfferService

    def setUp(self):
        super(ConfirmOfferFormTestCase, self).setUp()
        self.ocp.bank_id = '3333'
        self.ocp.save()

    def test_compare_xml(self):
        self.form.set_documents([
            {
                'name': 'Паспорт',
                'type': 'Копия паспорта представителя',
                'ext': 'png',
                'buffer': 'ppDcHSAf2lwl7myoxAv5t/TtgyhJxi8p8i/hhOSGXcX1',
            }
        ])
        payload = self.form.convert_order_to_bank_payload()
        self.assertEqual(payload, {
            'BrokerCode': 'CRED_IT_TEST',
            'ReleaseVsn': 'MultistepRTDMv2',
            'ListOfBrokerConfirmOffer': {
                'ApplicationPos': [
                    {
                        'ApplicationId': self.ocp.bank_id,
                        'ListOfOpportunityAttachment': {
                            'OpportunityAttachment': [
                                {'DocType': 'Копия паспорта представителя'},
                                {'OpptyFileName': 'Паспорт'},
                                {'OpptyFileExt': 'png'},
                                {'OpptyFileBuffer': 'ppDcHSAf2lwl7myoxAv5t/TtgyhJxi8p8i/hhOSGXcX1'},
                            ]
                        }
                    }
                ]
            }
        })


# class CheckScoreResultFormTestCase(BaseFormConversionMixin, BaseBankFormMixin, TestCase):
#     bank_name = BankBrand.POCHTA
#     bank_form = CheckScoreResultForm
#     service = CheckScoreResultService
#
#     def setUp(self):
#         super(CheckScoreResultFormTestCase, self).setUp()
#         self.ocp.bank_id = '3333'
#         self.ocp.save()
