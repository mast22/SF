from django.conf import settings
from ...base.forms import BaseBankForm


class CreateAgreementBankForm(BaseBankForm):
    """ Отправка ОТП подтверждения выбора заказа """

    mapper = {
        # Идентификатор среды ПО Кредитный Брокер
        'Environment_Code': {'converter': 'convert_calculated', 'callable': lambda _: settings.OTP_SW_CODE},
        # Код торговой точки в ПО Кредитный Брокер
        'TT_Ext_Code': {'converter': 'convert_method', 'method_name': 'get_outlet_code'},
        # Код агента
        'Agent_Ext_Code': {'converter': 'convert_method', 'method_name': 'get_agent_code'},
        # Код сети (партнера)
        'Chain_code': {'converter': 'convert_method', 'method_name': 'get_partner_code'},
        'Opty_Id': {'converter': 'convert_transform', 'lookup': 'chosen_product.bank_id', 'callable': lambda x: str(x)},
        'Paper_Tech': {'converter': 'convert_const', 'value': 'N'}
    }


class AuthorizeAgreementBankForm(BaseBankForm):
    mapper = {
        # Идентификатор среды ПО Кредитный Брокер
        'Environment_Code': {'converter': 'convert_calculated', 'callable': lambda _: settings.OTP_SW_CODE},
        # Код торговой точки в ПО Кредитный Брокер
        'TT_Ext_Code': {'converter': 'convert_method', 'method_name': 'get_outlet_code'},
        # Код агента
        'Agent_Ext_Code': {'converter': 'convert_method', 'method_name': 'get_agent_code'},
        # Код сети (партнера)
        'Chain_code': {'converter': 'convert_method', 'method_name': 'get_partner_code'},
        'Opty_Id': {'converter': 'convert_transform', 'lookup': 'chosen_product.bank_id', 'callable': lambda x: str(x)},
    }
