from apps.common.models import one_to_one_get_or_new
from apps.common.transitions import change_state
from ...base.service import BaseService
from ..forms import AuthorizeAgreementBankForm


class SendAuthorizationService(BaseService):
    wsdl_file = 'apps/banks_app/wsdl/otp/broker-authorize-agreement-api.wsdl'
    form_class = AuthorizeAgreementBankForm
    method = 'AuthorizeAgreement'
    endpoint = (
        '{http://siebel.com/CustomUI}AuthorizeAgreement',
        'https://broker-tst.otpbank.ru/broker-authorize-agreement-api/services'
    )

    def process_before(self):
        """ Ничего не нужно """
        pass

    def process_response(self, data):
        order = self.ocp.order
        contract = one_to_one_get_or_new(order, 'contract', creation_kwargs={})
        contract.bank_number = data.Agreement_Number
        contract.bank_authorization_code = data.Authorization_Code
        contract.bank_credit_amount = data.Credit_Amount
        contract.bank_goods_price = data.Goods_Price
        contract.save()
        change_state(order.set_authorized, 'Inner Error on setting AUTHORIZED status')
        order.save()
        return True
