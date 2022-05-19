from ...base.service import BaseService
# from ...pochta.forms. import


class DocsSignedService(BaseService):
    wsdl_file = 'apps/banks_app/wsdl/pochta/AfterScoring/BrokerServiceRegistry_25.wsdl'
    form_class = None
    method = 'docsSigned'
