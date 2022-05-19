from apps.common.models import one_to_one_get_or_new
from apps.common.transitions import change_state
from ...base.service import BaseService
from ..forms.confirm_offer import ConfirmOfferForm
from ...const import CreditProductStatus


class ConfirmOfferService(BaseService):
    wsdl_file = 'apps/banks_app/wsdl/pochta/AfterScoring/BrokerServiceRegistry_25.wsdl'
    form_class = ConfirmOfferForm
    method = 'confirmOffer'

    def process_before(self):
        pass

    def process_response(self, data):
        if data.ErrorCode and data.ErrorCode != '0':
            self.ocp.update_with_status(CreditProductStatus.TECHNICAL_ERROR, data.ErrorMessage)
            return False

        order = self.ocp.order
        # contract = one_to_one_get_or_new(order, 'contract', creation_kwargs={})
        # contract.bank_number = data.Agreement_Number
        # contract.bank_authorization_code = data.Authorization_Code
        # contract.bank_credit_amount = data.Credit_Amount
        # contract.bank_goods_price = data.Goods_Price
        # contract.save()
        change_state(order.set_authorized, 'Inner Error on setting AUTHORIZED status')
        order.save()
        return True

