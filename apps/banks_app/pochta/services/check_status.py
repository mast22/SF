from ...base.service import BaseService
# from ...pochta.forms. import


class CheckStatusService(BaseService):
    wsdl_file = 'apps/banks_app/wsdl/pochta/Scoring/1.CreateShortApplicationMQ/CreateShortApplication.wsdl'
    # form_class = CreateShortApplicationMQBankForm
    method = 'checkStatus'
