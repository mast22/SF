# from apps.orders.models import OrderCreditProduct


class BaseBankProvider:
    """Базовый класс провайдера для общения с банком."""
    REQUESTS_SETTINGS = {}

    def __init__(self, ocp: 'OrderCreditProduct', bank=None, order=None):
        self.ocp = ocp
        self.bank = bank if bank else ocp.credit_product.bank
        self.order = order if order else ocp.order

    def send_to_scoring(self):
        """ Отправка заявки на скоринг """
        NotImplementedError()

    def send_client_refused(self):
        """Отправка отказа клиента """
        NotImplementedError()

    def send_client_approve_ci(self):
        """ Отправка подтверждения клиента на проверку через БКИ """
        NotImplementedError()

    def send_agreement(self):
        """ Отправка запроса на выбор данного кредитного продукта клиентом """
        NotImplementedError()

    def send_documents(self):
        """ Отправить сканы подписанных документов """
        NotImplementedError()

    def send_authorization(self):
        """ Отправить подтверждение клиента о взятии кредита """
        NotImplementedError()
