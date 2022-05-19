
class PochtaMixin:
    """ Чтобы не плодить методов выделим некоторые отдельно """
    def get_bank_id(self) -> str:
        return self.ocp.bank_id
