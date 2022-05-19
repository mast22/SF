from django.conf import settings

from .pochta_mixin import PochtaMixin
from ...base.forms import BaseBankForm


class ConfirmOfferForm(PochtaMixin, BaseBankForm):
    mapper = {
        'BrokerCode': {'converter': 'convert_calculated', 'callable': lambda _: settings.POCHTA_SW_CODE},
        'ReleaseVsn': {'converter': 'convert_calculated', 'callable': lambda _: settings.POCHTA_API_VERSION},
        'ListOfBrokerConfirmOffer': {
            'converter': 'convert_list',
            'children_name': 'ApplicationPos',
            'fields': [
                {
                    'ApplicationId': {
                        'converter': 'convert_method',
                        'method_name': 'get_bank_id'
                    },
                    'ListOfOpportunityAttachment': {
                        'converter': 'convert_attached',
                        'children_name': 'OpportunityAttachment',
                        'patterns': [
                            {'key': 'type', 'name': 'DocType'},
                            {'key': 'name', 'name': 'OpptyFileName'},
                            {'key': 'ext', 'name': 'OpptyFileExt'},
                            {'key': 'buffer', 'name': 'OpptyFileBuffer'},
                        ]
                    }
                }
            ]
        }
    }
