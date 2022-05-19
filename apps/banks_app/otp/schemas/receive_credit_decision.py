from apps.common.soapfish import xsd


class ReceiveCreditDecisionRequest(xsd.ComplexType):
    INHERITANCE = None
    INDICATOR = xsd.Sequence
    environmentCode = xsd.Element(xsd.String)
    reference = xsd.Element(xsd.String)
    decision = xsd.Element(xsd.String)
    product = xsd.Element(xsd.String)
    amount = xsd.Element(xsd.Decimal)
    downPayment = xsd.Element(xsd.Decimal)
    creditTerm = xsd.Element(xsd.Decimal)
    referenceKB = xsd.Element(xsd.String, minOccurs=0)
    source = xsd.Element(xsd.String)
    monthlypaymentamount = xsd.Element(xsd.Decimal, minOccurs=0)
    requestForm = xsd.Element(xsd.String, minOccurs=0)
    requestFormComment = xsd.Element(xsd.String, minOccurs=0)
    CreditAmount = xsd.Element(xsd.String, minOccurs=0)
    FullAgentServicesAmount = xsd.Element(xsd.String, minOccurs=0)
    AgentServicesAmount = xsd.Element(xsd.String, minOccurs=0)
    limitCartOfGoods = xsd.Element(xsd.String, minOccurs=0)
    SMSBankAmount = xsd.Element(xsd.String, minOccurs=0)
    NeedNoConsent = xsd.Element(xsd.String, minOccurs=0)

    @classmethod
    def create(cls, environmentCode, reference, decision, product, amount, downPayment, creditTerm, source):
        instance = cls()
        instance.environmentCode = environmentCode
        instance.reference = reference
        instance.decision = decision
        instance.product = product
        instance.amount = amount
        instance.downPayment = downPayment
        instance.creditTerm = creditTerm
        instance.source = source
        return instance


class ReceiveCreditDecisionResponse(xsd.ComplexType):
    INHERITANCE = None
    INDICATOR = xsd.Sequence
    errorCode = xsd.Element(xsd.String, minOccurs=1)
    errorMessage = xsd.Element(xsd.String, minOccurs=0)

    @classmethod
    def create(cls, errorCode, errorMessage=None):
        instance = cls()
        instance.errorCode = errorCode
        instance.errorMessage = errorMessage
        return instance


ReceiveCreditDecisionSchema = xsd.Schema(
    imports=[],
    includes=[],
    targetNamespace='http://otpbank.ru/ReceiveCreditDecision',
    elementFormDefault='unqualified',
    simpleTypes=[],
    attributeGroups=[],
    groups=[],
    complexTypes=[ReceiveCreditDecisionRequest, ReceiveCreditDecisionResponse],
    elements={},
)
ReceiveCreditDecisionCustomUISchema = xsd.Schema(
    imports=[],
    includes=[],
    targetNamespace='http://siebel.com/CustomUI',
    elementFormDefault='qualified',
    simpleTypes=[],
    attributeGroups=[],
    groups=[],
    complexTypes=[],
    elements={
        'ReceiveCreditDecisionRequest': xsd.Element(__name__ + '.ReceiveCreditDecisionRequest'),
        'ReceiveCreditDecisionResponse': xsd.Element(__name__ + '.ReceiveCreditDecisionResponse')
    },
)