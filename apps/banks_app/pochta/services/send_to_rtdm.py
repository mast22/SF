from ...base.service import BaseService
from ..forms.send_to_rtdm_mq import SendToRTDMMQForm
from ...const import CreditProductStatus


class SendToRTDMService(BaseService):
    wsdl_file = 'apps/banks_app/wsdl/pochta/Scoring/3.SendToRTDMMQ/SendToRTDM.wsdl'
    form_class = SendToRTDMMQForm
    method = 'SendToRTDM'

    def process_before(self):
        pass

    def process_response(self, data):
        if str(data.ErrorCode) != '0':
            self.ocp.update_with_status(CreditProductStatus.TECHNICAL_ERROR, data.ErrorMessage,
                    required_fields=data.RequiredInfo)
            return False
        return True
