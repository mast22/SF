from ...base.service import BaseService
from ..forms import AddDocOpty


class SendDocumentsService(BaseService):
    wsdl_file = 'apps/banks_app/wsdl/otp/broker-add-doc-opty-api.wsdl'
    form_class = AddDocOpty
    method = 'AddDocOptyOperation'
    endpoint = (
        '{http://siebel.com/CustomUI}AddDocOptyBinding',
        'https://broker-tst.otpbank.ru/broker-add-doc-opty-api/services'
    )

    def process_response(self, data):
        pass

    def process_before(self):
        pass
