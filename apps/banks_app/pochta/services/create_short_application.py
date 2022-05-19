from ...base.service import BaseService
from ..forms.create_short_application_mq import CreateShortApplicationMQBankForm
from apps.orders.const import CreditProductStatus


class CreateShortApplicationService(BaseService):
    wsdl_file = 'apps/banks_app/wsdl/pochta/Scoring/1.CreateShortApplicationMQ/CreateShortApplication.wsdl'
    form_class = CreateShortApplicationMQBankForm
    method = 'CreateShortApplication'

    def process_before(self):
        self.ocp.update_with_status(CreditProductStatus.IN_PROCESS)

    def process_response(self, response):
        if str(response.ErrorCode) == '0':
            # В отличии от ОТП мы не ожидаем получить ответ о скоринге сразу, подтверждение скоринга мы получим
            # из асинхронной задачи
            self.ocp.update_with_status(CreditProductStatus.IN_PROCESS, save=False)
        else:
            self.ocp.update_with_status(CreditProductStatus.TECHNICAL_ERROR, response.ErrorMessage, save=False)

        self.ocp.bank_id = response.ApplicationIntId
        self.ocp.save()
