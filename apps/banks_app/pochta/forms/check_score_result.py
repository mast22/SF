from django.conf import settings

from .pochta_mixin import PochtaMixin
from ...base.forms import BaseBankForm


class CheckScoreResultForm(PochtaMixin, BaseBankForm):
    mapper = {
        'BrokerCode': {'converter': 'convert_calculated', 'callable': lambda _: settings.POCHTA_SW_CODE},
        'ReleaseVsn': {'converter': 'convert_calculated', 'callable': lambda _: settings.POCHTA_API_VERSION},
        'ApplicationId': {
            'converter': 'convert_method',
            'method_name': 'get_bank_id'
        },
    }
