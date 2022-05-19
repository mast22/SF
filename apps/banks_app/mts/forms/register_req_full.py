import datetime

from apps.common.utils import value_or_zero
from apps.misc.const import AccordanceSpecifier
from apps.orders.const import Sex, MaritalStatus, Education, WorkplaceCategory, WorkerSocialStatus
from apps.orders.models import Order
from apps.partners.const import LocalityType
from serv_finance import settings
from .register_req_common import client_list_document, total_outlay, total_income, client_list_work, citizenship, \
    client_common_data, client_list_address, specific_data
from .register_req_middle import get_mts_dependents_count
from ...base.forms import BaseBankForm
import uuid


def get_mts_request_id(order: Order):
    """ Из документации МТС
    Уникальный. Генерируется на стороне Брокера с соответствующим префиксом.
    Пример ***_1234567, где *** - префикс торговой сети или брокера
    TODO Узнать что такое префикс торговой сети
    """
    return "1234_1234"


MTS_MARTIAL_STATUS_MAPPING = {
    MaritalStatus.SINGLE: 'FAMILY.STATUS.1',
    MaritalStatus.MARRIED: 'FAMILY.STATUS.2',
    MaritalStatus.CIVIL: 'FAMILY.STATUS.5',
    MaritalStatus.DIVORCED: 'FAMILY.STATUS.4',
    MaritalStatus.WIDOWED: 'FAMILY.STATUS.3',
}

MTS_EDUCATION_MAPPING = {
    Education.ACADEMIC_DEGREE: 'EDUCATION.LEVEL.6',
    Education.SEVERAL_DEGREES: 'EDUCATION.LEVEL.6',
    Education.HIGHER: 'EDUCATION.LEVEL.5',
    Education.HIGHER_INCOMPLETE_EDUCATION: 'EDUCATION.LEVEL.4',
    Education.SPECIALIZED_SECONDARY: 'EDUCATION.LEVEL.3',
    Education.SECONDARY: 'EDUCATION.LEVEL.2',
    Education.SECONDARY_INCOMPLETE: 'EDUCATION.LEVEL.1',
}


class RegisterReqFullBankForm(BaseBankForm):
    """ Полная форма создания заказа в МТС банке
    Работа приостановлена, пока разрабатываем среднюю заявку
    """

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
            'value': 'FULL'
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
    },
