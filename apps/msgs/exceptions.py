
class ProviderError(Exception):
    """Ошибка при выполнении запроса на отправку SMS-сообщения"""


class ProviderBadResponseError(ProviderError):
    """Ошибочный статус ответа провайдера"""


class ProviderKeyError(ProviderError, KeyError):
    """Один из аргументов не задан или задан не корректно"""
