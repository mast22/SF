

class BankError(Exception):
    """Общий класс исключений при работе с банками"""


class ResponseIsEmpty(BankError):
    """Запрос к api банка не вернул ответ"""


class FaultyRequestException(BankError):
    """Ошибка в запросе к банку"""
    pass
