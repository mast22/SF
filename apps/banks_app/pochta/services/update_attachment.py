from ...base.service import BaseService
from ..forms.update_attachment_mq import UpdateAttachmentMQBankForm
from ...const import CreditProductStatus


class UpdateAttachmentService(BaseService):
    wsdl_file = 'apps/banks_app/wsdl/pochta/Scoring/4.UpdateAttachmentMQ/UpdateAttachment.wsdl'
    form_class = UpdateAttachmentMQBankForm
    method = 'UpdateAttachment'

    def process_before(self):
        pass

    def process_response(self, data):
        if str(data.ErrorCode) != '0':
            self.ocp.update_with_status(CreditProductStatus.TECHNICAL_ERROR)
