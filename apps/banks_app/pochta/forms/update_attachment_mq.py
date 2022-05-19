from django.conf import settings

from ...base.forms import BaseBankForm


class UpdateAttachmentMQBankForm(BaseBankForm):
    mapper = {
        'BrokerCode': {'converter': 'convert_calculated', 'callable': lambda _: settings.POCHTA_SW_CODE},
        'ReleaseVsn': {'converter': 'convert_calculated', 'callable': lambda _: settings.POCHTA_API_VERSION},
        'ApplicationIntId': {'converter': 'convert_const', 'value': 'APP_ID'},
        'ListOfContacts': {
            'converter': 'convert_dict',
            'data': {
                'Contact': {
                    'converter': 'convert_dict',
                    'data': {
                        'ContactId': {'converter': 'convert_const', 'value': 'ИД слепка'},
                        'ListOfAttachments': {
                            'converter': 'convert_list',
                            'children_name': 'Attachment',
                            'fields': [
                                # Почта требует только фото клиента
                                {
                                    'OpptyFileType': {
                                        'converter': 'convert_const',
                                        'value': 'Photo',
                                    },
                                    'OpptyFileName': {
                                        'converter': 'convert_method',
                                        'lookup': 'passport.client_photo',
                                        'method_name': 'cast_filename',
                                    },
                                    'OpptyFileExt': {
                                        'converter': 'convert_method',
                                        'lookup': 'passport.client_photo',
                                        'method_name': 'cast_file_extension'
                                    },
                                    'OpptyFile': {
                                        'converter': 'convert_method',
                                        'lookup': 'passport.client_photo',
                                        'method_name': 'cast_file_base64',
                                    },
                                },
                            ],
                        }
                    }
                }
            }
        }
    }
