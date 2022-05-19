import datetime

from apps.common.utils import value_or_zero
from apps.orders.const import Sex
from apps.orders.models import Order
from serv_finance import settings
from .register_req_common import client_list_document, total_outlay, client_list_address, client_list_work, \
    total_income, citizenship, client_common_data, specific_data
from ...base.forms import BaseBankForm
import uuid


def get_mts_request_id(order: Order):
    """ Из документации МТС
    Уникальный. Генерируется на стороне Брокера с соответствующим префиксом.
    Пример ***_1234567, где *** - префикс торговой сети или брокера
    TODO Узнать что такое префикс торговой сети
    """
    return "1234_1234"


def get_mts_dependents_count(order: Order):
    """ МТС принимает только кол-во иждивенцев, поэтому мы добавляем к ним кол-во детей """
    return value_or_zero(order.family_data.children_count) + value_or_zero(order.family_data.dependents_count)


class RegisterReqMiddleBankForm(BaseBankForm):
    """ Средняя форма создания заказа в МТС банке """

    mapper = {
        'mtsRequestId': {
            'converter': 'convert_calculated',
            'callable': get_mts_request_id
        },
        'messageId': {
            'converter': 'convert_calculated',
            'callable': lambda _: str(uuid.uuid4()),
        },
        'messageType': {
            'converter': 'convert_const',
            'value': 'REGISTER_REQ_BRK'
        },
        'messageDateTime': {
            # Дата-Время на стороне КБ - YYYY-MM-DDTH24:MI:SS;
            'converter': 'convert_calculated',
            'callable': lambda _: datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        },
        'SPName': {'converter': 'convert_calculated', 'callable': lambda _: settings.MTS_SW_CODE},
        'MsgReceiver': {
            'converter': 'convert_const',
            'value': 'SIEBEL'
        },
        'isEDS': {
            'converter': 'convert_const',
            'value': 'false'
        },
        'questionnaireType': {
            'converter': 'convert_const',
            'value': 'MIDDLE'
        },
        'ServerInfo': {
            'converter': 'convert_dict',
            'data': {
                'MsgType': {
                    'converter': 'convert_const',
                    'value': 'REGISTER_REQ_BRK',
                },
            }
        },
        'MTSPOSSpecificData': specific_data,
        'request': {
            'converter': 'convert_dict',
            'data': {
                'clientComplexData': {
                    'converter': 'convert_dict',
                    'data': {
                        'client': {
                            'converter': 'convert_dict',
                            'data': {
                                'clientCommonData': client_common_data,
                                'clientListDocument': client_list_document,
                                'clientListAddress': client_list_address,
                                'clientListContact': {
                                    'converter': 'convert_list',
                                    'children_name': 'clientContact',
                                    'fields': [
                                        {
                                            'contactType': {
                                                'converter': 'convert_transform',
                                                'lookup': 'client_order.phone',
                                                'callable': lambda phone: phone.as_e164
                                            },
                                            'isPrimary': {'converter': 'convert_const', 'value': 'true'}
                                        }
                                    ]
                                },
                                'clientListWork': client_list_work,
                            }
                        }
                    },
                }
            }
        }
    }
