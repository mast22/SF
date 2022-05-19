from django.conf import settings

from ...base.forms import BaseBankForm


class SendToRTDMMQForm(BaseBankForm):
    mapper = {
        'BrokerCode': {'converter': 'convert_calculated', 'callable': lambda _: settings.POCHTA_SW_CODE},
        'ReleaseVsn': {'converter': 'convert_calculated', 'callable': lambda _: settings.POCHTA_API_VERSION},
        'Application': {
            'converter': 'convert_dict',
            'data': {
                'ApplicationIntId': {
                    'converter': 'convert_const',
                    'value': 'App_id',
                },
            }
        }
    }
