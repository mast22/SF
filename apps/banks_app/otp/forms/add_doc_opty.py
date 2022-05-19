from ...base.forms import BaseBankForm
from django.conf import settings


class AddDocOpty(BaseBankForm):
    mapper = {
        # Идентификатор среды ПО Кредитный Брокер
        'Environment_Code': {'converter': 'convert_calculated', 'callable': lambda _: settings.OTP_SW_CODE},
        # Код торговой точки в ПО Кредитный Брокер
        'TT_Ext_Code': {'converter': 'convert_method', 'method_name': 'get_outlet_code'},
        # Код агента
        'Agent_Ext_Code': {'converter': 'convert_method', 'method_name': 'get_agent_code'},
        # Код сети (партнера)
        'Chain_code': {'converter': 'convert_method', 'method_name': 'get_partner_code'},
        'Opty_Id': {'converter': 'convert_transform', 'lookup': 'id', 'callable': lambda x: str(x)},
        'ListOfOpportunityAttachment': {
            'converter': 'convert_attached',
            'children_name': 'OpportunityAttachment',
            'patterns': [
                {'key': 'type', 'name': 'DocumentType'},
                {'key': 'name', 'name': 'OpptyFileName'},
                {'key': 'ext', 'name': 'OpptyFileExt'},
                {'key': 'buffer', 'name': 'OpptyFileBuffer'},
            ]
        }
    }
