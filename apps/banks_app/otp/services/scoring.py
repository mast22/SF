from ... import logger
from ...base.service import BaseService
from ..forms import CreateOptyBankForm
from ...const import CreditProductStatus


class ScoringService(BaseService):
    wsdl_file = 'apps/banks_app/wsdl/otp/broker-create-opty-api.wsdl'
    form_class = CreateOptyBankForm
    method = 'CreateOpty_spcv2'
    endpoint = (
        '{http://siebel.com/CustomUI}CreateOpty_spcv2',
        'https://broker-tst.otpbank.ru/broker-create-opty-api/services'
    )

    def process_before(self):
        self.ocp.update_with_status(CreditProductStatus.IN_PROCESS)

    def process_response(self, data):
        if str(data.Error_Code) == '0':
            logger.debug('Set scoring response success')
            self.ocp.update_with_status(CreditProductStatus.SUCCESS, save=False)
        else:
            logger.debug('Failure')
            self.ocp.update_with_status(CreditProductStatus.TECHNICAL_ERROR, data.Error_Message, save=False)
        self.ocp.bank_id = data.Opty_Id
        self.ocp.save()
