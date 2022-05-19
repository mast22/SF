from dataclasses import dataclass
from collections import namedtuple
from typing import Optional

from django.utils.translation import gettext_lazy as __
from apps.common.choices import Choices


class BankPriorityChoice(Choices):
    FIRST = 1, '1'
    SECOND = 2, '2'
    THIRD = 3, '3'
    FORTH = 4, '4'
    FIFTH = 5, '5'


class BankBrand(Choices):
    OTP = 'OTP', __('OTП Банк')
    ALFA = 'ALFA', __('Альфа Банк')
    POCHTA = 'POCHTA', __('Почта Банк')
    MTS = 'MTS', __('МТС Банк')


class ExtraServiceType(Choices):
    BASIC = 'basic', __('Основная услуга')
    CUSTOM = 'custom', __('Другое')


class ExtraServicePriceType(Choices):
    PERCENT = 'percent', __('Процент от суммы кредита')
    CURRENCY = 'currency', __('Твёрдая сумма')


@dataclass(repr=True, frozen=True)
class ScoringResponse:
    accepted: bool = True
    decision_code: Optional[str] = None
    details: Optional[str] = None
    bank_id: Optional[str] = None


@dataclass(frozen=True, repr=True)
class SendToScoringResponse:
    """ Результат установки заказа в очередь скоринга """
    bank_id: Optional[str] = None
    decision_code: Optional[str] = None
    details: Optional[str] = None


# noinspection PyArgumentList
ScoringCallbackResult = namedtuple(
    # Данные из обратного запроса банка с результатами по скорингу
    'ScoringCallbackResult',
    ('result', 'status', 'bank_order', 'error_code', 'error_details', 'data'),
    defaults=(False, None, None, None, None)
)

# noinspection PyArgumentList
AgentCreditProductAttributes = namedtuple(
    # Внутренние данные в сериалайзере AgentCreditProduct
    'AgentCreditProductAttributes',
    ('monthly_payment', 'overpayment', 'agent_commission',),
    defaults=(None, None, None)
)

# noinspection PyArgumentList
IsResponseProcessable = namedtuple(
    # Ответ на запрос на скоринг в банк
    'ScoringResult',
    ('accepted', 'error_code', 'error_details', 'bank_id'),
    defaults=(True, None, None, None)
)
