import mimetypes
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

from apps.common import utils as u
from apps.common.models import one_to_one_get_or_new
from apps.orders.const import CreditProductStatus
from apps.orders.models import DocumentToSign
from apps.orders_ws.shortcuts import send_message_sync, WSMessageType
from ...base.service import BaseService
from ..forms.get_docs import GetDocsForm


class GetDocumentsService(BaseService):
    wsdl_file = 'apps/banks_app/wsdl/pochta/AfterScoring/BrokerServiceRegistry_25.wsdl'
    form_class = GetDocsForm
    method = 'getDocs'

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
        contract.bank_number = data.AgreementNumber
        contract.save()

        if str(data.Error_Code) != '0':
            self.ocp.update_with_status(CreditProductStatus.TECHNICAL_ERROR, data.Error_Message)
            order.set_agreement_error()
            return
        # 2. Сохранить сканы документов. Сложить в contract.filled_in_forms
        doc_ids = []
        # data.ListOfBrokerApplicationPf[].ApplicationPos.ListOfOpportunityPf.OpportunityPf
        for document in data.ListOfBrokerApplicationPf.ApplicationPos.ListOfOpportunityPf.OpportunityPf:
            doc_type = document.OpptyFileSrcType
            doc_ext = document.DocumentName.lower().split('.')[-1] if document.DocumentName else 'txt'
            doc_mimetype = mimetypes.types_map.get('.' + doc_ext, 'text/plain')
            doc_name = f'order_{order.id}_document_{u.generate_random_uuid()}.{doc_ext}'
            doc_file_bytes = document.OpptyFileBuffer
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
