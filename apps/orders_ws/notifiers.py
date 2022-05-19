"""
Методы для отправки конкретных сообщений клиенту.
"""
from .const import WSMessageType
from .shortcuts import send_message_sync


def notify_scoring_error(ocp, error_text):
    """"""
    send_message_sync(
        ocp.order.agent_id, ocp.order_id, WSMessageType.SCORING_ERROR,
        data=dict(order_credit_product=ocp.id, error_text=error_text)
    )


def notify_scoring_result(ocp, scoring_status):
    """"""
    send_message_sync(
        ocp.order.agent_id, ocp.order_id, WSMessageType.SCORING_RESULT,
        data=dict(
            order_credit_product=ocp.id,
            credit_product=ocp.credit_product.id,
            scoring_status=scoring_status
        )
    )


def notify_sending_to_scoring(ocp):
    """"""
    send_message_sync(
        ocp.order.agent_id,
        ocp.order_id,
        WSMessageType.SENDING_TO_SCORING,
        data=dict(
            order_credit_product=ocp.id,
            bank=ocp.credit_product.bank.name,
        )
    )



# TODO: сделать shortcut-ы для данных типов WS-уведомлений:
# DOCUMENTS_TO_SIGN = 'documents_to_sign', __('Пришли печатные формы для подписания договора')
# AGREEMENT_ACCEPTED = 'agreement_accepted', __('Банк принял договор на оформление кредита')
# AGREEMENT_REJECTED = 'agreement_rejected', __('Банк отвергнул договор на оформление кредита')
# REQUEST_ERROR = 'request_error', __('Ошибка при вызове сервиса')

