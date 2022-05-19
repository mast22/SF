from ...base.service import BaseService
from ..forms import RejectOptyBankForm
from ...const import CreditProductStatus


class ClientRefusedService(BaseService):
    """ Оповещения банка о отказе клиента, вызов обработки не требуется """
    wsdl_file = 'apps/banks_app/wsdl/otp/broker-reject-opty-api.wsdl'
    form_class = RejectOptyBankForm
    method = 'Cancel'
    endpoint = (
        '{http://siebel.com/CustomUI}Cancel',
        'https://broker-tst.otpbank.ru/broker-reject-opty-api/services',
    )

    def process_before(self):
        self.ocp.update_with_status(CreditProductStatus.CLIENT_REFUSED)

    def process_response(self, data):
        if str(data.Error_Code) != "0":
            self.ocp.explanation = "Запрос отказа клиента завершился ошибкой"
            self.ocp.update_with_status(CreditProductStatus.TECHNICAL_ERROR, bank_data=data.Error_Message)
