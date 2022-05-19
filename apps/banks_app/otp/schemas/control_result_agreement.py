from apps.common.soapfish import xsd


class IntegrationIdType(xsd.String):
    pattern = r'[*]{0}|[0-9A-Fa-f]{48}'


class NonEmptyString(xsd.String):
    pass


class PhoneType(xsd.String):
    pattern = r'[+]7[0-9]{10}'


class SiebelBooleanType(xsd.String):
    enumeration = ['Y', 'N']


class SiebelDate(xsd.String):
    pattern = r'[0-9]{2}/[0-9]{2}/[0-9]{4}'


ControlResultAgreementModelTypesSchema = xsd.Schema(
    imports=[],
    includes=[],
    targetNamespace='http://otpbank.ru/Model/Types',
    elementFormDefault='unqualified',
    simpleTypes=[IntegrationIdType, NonEmptyString, PhoneType, SiebelBooleanType, SiebelDate],
    attributeGroups=[],
    groups=[],
    complexTypes=[],
    elements={},
)


class ControlResultAgreementRequest(xsd.ComplexType):
    INHERITANCE = None
    INDICATOR = xsd.Sequence
    environmentCode = xsd.Element(xsd.String)
    optyID = xsd.Element(xsd.String)
    checkResult = xsd.Element(xsd.String)
    comment = xsd.Element(xsd.String)

    @classmethod
    def create(cls, environmentCode, optyID, checkResult, comment, opportunityAttachment):
        instance = cls()
        instance.environmentCode = environmentCode
        instance.optyID = optyID
        instance.checkResult = checkResult
        instance.comment = comment
        instance.opportunityAttachment = opportunityAttachment
        return instance


class ControlResultAgreementResponse(xsd.ComplexType):
    INHERITANCE = None
    INDICATOR = xsd.Sequence
    Error_Code = xsd.Element(xsd.String, minOccurs=1)
    Error_Message = xsd.Element(xsd.String, minOccurs=0)

    @classmethod
    def create(cls, Error_Code, errorMessage=None):
        instance = cls()
        instance.Error_Code = Error_Code
        instance.errorMessage = errorMessage
        return instance


ControlResultAgreementSchema = xsd.Schema(
    imports=[],
    includes=[],
    targetNamespace='http://otpbank.ru/ControlResultAgreement',
    elementFormDefault='unqualified',
    simpleTypes=[],
    attributeGroups=[],
    groups=[],
    complexTypes=[ControlResultAgreementRequest, ControlResultAgreementResponse],
    elements={},
)
ControlResultAgreementCustomUISchema = xsd.Schema(
    imports=[],
    includes=[],
    targetNamespace='http://siebel.com/CustomUI',
    elementFormDefault='qualified',
    simpleTypes=[],
    attributeGroups=[],
    groups=[],
    complexTypes=[],
    elements={
        'ControlResultAgreementRequest': xsd.Element(__name__ + '.ControlResultAgreementRequest'),
        'ControlResultAgreementResponse': xsd.Element(__name__ + '.ControlResultAgreementResponse')
    },
)