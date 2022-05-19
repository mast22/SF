from django.conf import settings

from ..provider import OTPBankProvider
from ..schemas import receive_credit_decision as s
from apps.common.soapfish import soap, xsd
from apps.common.soapfish.django_ import django_dispatcher
from .common import get_ocp


def otp_receive_credit_decision(receive_credit_decision_data):
    ocp = get_ocp(receive_credit_decision_data.reference)

    if ocp is None: return
    # OCP может быть не найден в случае редиректа запроса с боевого на тестовый
    # Либо если запрос на скоринг был отправлен с тестового и чтобы проигнорировать его на боевом
    provider = OTPBankProvider(ocp=ocp, bank=ocp.credit_product.bank, order=ocp.order)
    provider.process_scoring_callback(receive_credit_decision_data)


def receive_credit_decision(request, ReceiveCreditDecisionRequest):
    # TODO: Алексей говорил про авторизацию, необходимо это рассмотреть
    # TODO: Можно заменить на асинх. задачу

    otp_receive_credit_decision(ReceiveCreditDecisionRequest)
    return s.ReceiveCreditDecisionResponse.create(errorCode='0')


receive_credit_decision_method = xsd.Method(
    function=receive_credit_decision,
    soapAction='test',
    input='ReceiveCreditDecisionRequest',
    inputPartName='ReceiveCreditDecisionRequest',
    output='ReceiveCreditDecisionResponse',
    outputPartName='ReceiveCreditDecisionResponse',
    operationName='receiveCreditDecision',
)

credit_decision_port_service = soap.Service(
    name='CreditDecisionPort',
    targetNamespace='http://siebel.com/CustomUI',
    location='${scheme}://${host}/services',
    schemas=[s.ReceiveCreditDecisionSchema, s.ReceiveCreditDecisionCustomUISchema],
    version=soap.SOAPVersion.SOAP11,
    methods=[receive_credit_decision_method],
)


resend_to_kwarg = {}
if settings.REDIRECT_CALLBACKS_TO_STAGE:
    resend_to_kwarg = {
        # 'resend_to': 'http://188.225.44.163/api/soap/otp/receive-credit-decision',
        'resend_to': 'http://broker.cred-it.rdbx24.ru/api/bank/callback/otp-bank',
    }

callback_receive_credit_decision = django_dispatcher(
    credit_decision_port_service,
    **resend_to_kwarg
)
