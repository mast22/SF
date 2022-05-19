import mimetypes
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

from apps.common import utils as u
from apps.common.models import one_to_one_get_or_new
from apps.orders.const import CreditProductStatus
from apps.orders.models import DocumentToSign
from apps.orders_ws.shortcuts import send_message_sync, WSMessageType
from ...base.service import BaseService
from ..forms import CreateAgreementBankForm


class CreateAgreementService(BaseService):
    wsdl_file = 'apps/banks_app/wsdl/otp/broker-create-agreement-api.wsdl'
    form_class = CreateAgreementBankForm
    method = 'CreateAgreement'
    endpoint = (
        '{http://siebel.com/CustomUI}CreateAgreement',
        'https://broker-tst.otpbank.ru/broker-create-agreement-api/services',
    )

    def process_before(self):
        order = self.ocp.order
        order.set_documents_creation()
        order.save()

    def process_response(self, data):
        """Обработка ответа на отправку согласия клиента на получение кредита
        CreateAgreement
        """
        order = self.ocp.order
        # 1. Сохранить Agreement_Number и инфу об Agreement в Agreement или Contract (?)
        contract = one_to_one_get_or_new(order, 'contract', creation_kwargs={})
        contract.bank_number = data.Agreement_Number
        contract.save()

        if str(data.Error_Code) != '0':
            self.ocp.update_with_status(CreditProductStatus.TECHNICAL_ERROR, data.Error_Message)
            order.set_agreement_error()
            return
        # 2. Сохранить сканы документов. Сложить в contract.filled_in_forms
        doc_ids = []
        for document in data.ListOfDocumentations.Document:
            doc_type = document.Document_Type
            doc_ext = document.Document_Ext.lower() if document.Document_Ext else 'txt'
            doc_mimetype = mimetypes.types_map.get('.' + doc_ext, 'text/plain')
            doc_name = f'order_{order.id}_document_{u.generate_random_uuid()}.{doc_ext}'
            doc_file_bytes = document.Document_Buffer
            doc_file = InMemoryUploadedFile(
                file=BytesIO(doc_file_bytes), field_name='file',
                name=doc_name, content_type=doc_mimetype,
                size=len(doc_file_bytes), charset='utf-8'
            )
            doc = DocumentToSign.objects.create(
                order=order, file=doc_file,
                file_name=doc_type, file_ext=doc_ext
            )
            doc_ids.append(doc.id)
        order.set_documents_signing()
        order.save()
        # 3. Отправить по ws уведомление, что печатные формы сохранены в модель order.
        send_message_sync(order.agent_id, order.id, type=WSMessageType.DOCUMENTS_TO_SIGN, data={'documents': doc_ids, })
        return True
