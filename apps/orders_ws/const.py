from apps.common.choices import Choices
from django.utils.translation import gettext_lazy as __


class WSMessageType(Choices):
    """Типы уведомлений, которые можно получить по websocket-протоколу"""

    PASSPORT_RECOGNIZED = 'passport_recognized', __('Паспортные данные распознаны')
    SCORING_ERROR = 'scoring_error', __('Ошибка при отправке заявки на скоринг')
    SCORING_RESULT = 'scoring_result', __('Пришёл результат скоринга от банка')
    DOCUMENTS_TO_SIGN = 'documents_to_sign', __('Пришли печатные формы для подписания договора')
    AGREEMENT_ACCEPTED = 'agreement_accepted', __('Банк принял договор на оформление кредита')
    AGREEMENT_REJECTED = 'agreement_rejected', __('Банк отвергнул договор на оформление кредита')
    SENDING_TO_SCORING = 'sending_to_scoring', __('Заказ был отправлен на скоринг')
    REQUEST_ERROR = 'request_error', __('Ошибка при вызове сервиса')


class WSMessageError(Choices):
    BEARER_NOT_PROVIDED = 'bearer_not_provided', __('Bearer не был предоставлен')
    TOKEN_IS_OUTDATED = 'token_is_outdated', __('Токен не найден, возможно он устарел')
    WRONG_TOKEN_FORM = 'wrong_token_form', __('Неправильная форма токена, попробуйте "Authorization: Token <token>"')
    CANT_DECODE = 'cant_decode', __('Невозможно декодировать JSON. Удостоверьтесь, что вы отправляете валидный JSON')
    INCOMING_MESSAGES_ARE_NOT_ALLOWED = 'incoming_messages_are_not_allowed', __('Входящие сообщения запрещены')
