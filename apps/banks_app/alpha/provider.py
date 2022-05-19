from ..base.provider import BaseBankProvider


class AlphaBankProvider(BaseBankProvider):
    """Прослойка для работы с api альфа-банка."""

    def get_credit_products_inner(self):
        return None

    def get_extra_services_inner(self):
        return None

    def send_to_scoring_inner(self, order):
        return None
