from ... import logger

from ..provider import OTPBankProvider
from apps.common.soapfish import soap, xsd
from apps.common.soapfish.django_ import django_dispatcher
from ..schemas import control_result_agreement as s
from .common import get_ocp


def otp_process_control_result_agreement(control_result_agreement_data):
    ocp = get_ocp(control_result_agreement_data.OptyID)

    if ocp is None: return

    # Выполним требуемую логику по коллбеку
    provider = OTPBankProvider(ocp=ocp)
    provider.process_agreement_callback(control_result_agreement_data) # TODO асинхронка


def control_result_agreement(request, control_result_agreement_data):
    otp_process_control_result_agreement(control_result_agreement_data)
    logger.info(f'Bank callback OTP.ControlResultAgreement. request: {request},'
                f' ControlResultAgreementRequest: {control_result_agreement_data}')
    return s.ControlResultAgreementResponse(errorCode='0', errorMessage='message ok')


ControlResultAgreement_method = xsd.Method(
    function=control_result_agreement,
    soapAction='',
    input='ControlResultAgreementRequest',
    inputPartName='ControlResultAgreementRequest',
    output='ControlResultAgreementResponse',
    outputPartName='ControlResultAgreementResponse',
    operationName='ControlResultAgreement',
)

ControlResultAgreement_SERVICE = soap.Service(
    name='ControlResultAgreement',
    targetNamespace='http://siebel.com/CustomUI',
    location='${scheme}://${host}/services',
    schemas=[
        s.ControlResultAgreementModelTypesSchema,
        s.ControlResultAgreementSchema,
        s.ControlResultAgreementCustomUISchema,
    ],
    version=soap.SOAPVersion.SOAP11,
    methods=[ControlResultAgreement_method],
)

callback_control_result_agreement = django_dispatcher(ControlResultAgreement_SERVICE)
