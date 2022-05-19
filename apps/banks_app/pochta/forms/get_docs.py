from django.conf import settings

from .pochta_mixin import PochtaMixin
from ...base.forms import BaseBankForm


class GetDocsForm(PochtaMixin, BaseBankForm):
    mapper = {
        'BrokerCode': {'converter': 'convert_calculated', 'callable': lambda _: settings.POCHTA_SW_CODE},
        'ReleaseVsn': {'converter': 'convert_const', 'value': 'MultistepRTDMv2'},
        'ApplicationId': {
            'converter': 'convert_method',
            'method_name': 'get_bank_id'
        },
    }


class DocsSignedForm(PochtaMixin, BaseBankForm):
    """
    TODO узнать у СФ как они работают по документам в почта-банке
    TODO: должно генерить структуру, из которой получится следующее:
    <xsd:element name="BrokerCode" type="xsd:string" minOccurs="1" maxOccurs="1"/>
    <xsd:element name="ReleaseVsn" type="xsd:string" minOccurs="0" maxOccurs="1"/>
    <xsd:element ref="xsdLocal5:ListOfBrokerConfirmOffer"/>
        <xsd:complexType name="ListOfBrokerConfirmOfferTopElmt">
            <xsd:sequence>
                <xsd:element maxOccurs="1" minOccurs="1" name="ListOfBrokerConfirmOffer"
                     type="xsdLocal1:ListOfBrokerConfirmOffer"/>
            </xsd:sequence>
        </xsd:complexType>
    """

    mapper = {
        'BrokerCode': {'converter': 'convert_calculated', 'callable': lambda _: settings.POCHTA_SW_CODE},
        'ReleaseVsn': {'converter': 'convert_calculated', 'callable': lambda _: settings.POCHTA_API_VERSION},
        'ListOfBrokerConfirmOffer': {
            'converter': 'convert_dict',
            'data': {
                'ApplicationId': {
                    'converter': 'convert_method',
                    'method_name': 'get_bank_id'
                },
                'ListOfOpportunityAttachment': {
                    'converter': 'convert_list',
                    'children_name': 'OpportunityAttachment',
                    'fields': []
                }
            }
        }
    }


class CheckStatusForm(PochtaMixin, BaseBankForm):
    """
    TODO: должно генерить структуру, из которой получится следующее:
    <xsd:element name="checkStatus_Input">
        <xsd:complexType>
            <xsd:sequence>
                <xsd:element name="BrokerCode" type="xsd:string" minOccurs="1" maxOccurs="1"/>
                <xsd:element name="ReleaseVsn" type="xsd:string" minOccurs="0" maxOccurs="1"/>
                <xsd:element name="ApplicationId" type="xsd:string"/>
            </xsd:sequence>
        </xsd:complexType>
    </xsd:element>
    """
    mapper = {
        'BrokerCode': {'converter': 'convert_calculated', 'callable': lambda _: settings.POCHTA_SW_CODE},
        'ReleaseVsn': {'converter': 'convert_calculated', 'callable': lambda _: settings.POCHTA_API_VERSION},
        'ApplicationId': {
            'converter': 'convert_method',
            'method_name': 'get_bank_id'
        },
    }

