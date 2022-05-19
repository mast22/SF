from .services.check_score_result import CheckScoreResultService
from ..base.provider import BaseBankProvider
from ..base.exceptions import BankError
from .services.create_short_application import CreateShortApplicationService
from .services.update_attachment import UpdateAttachmentService
from .services.send_to_rtdm import SendToRTDMService


class PochtaBankProvider(BaseBankProvider):
    def send_to_scoring(self):
        """ Отправка анкеты и документов на скоринг """
        # Отправляем анкету. мы отправляет как можно больше данных в одном запросе
        create_short_application_service = CreateShortApplicationService(self.ocp)
        result = create_short_application_service.evaluate()
        if not result:
            return result

        # Отправляем фотографии клиента
        update_attachment_service = UpdateAttachmentService(self.ocp)
        result = update_attachment_service.evaluate()
        if not result:
            return result

        # Отправляем заявку на проверку
        send_to_rtdm_service = SendToRTDMService(self.ocp)
        result = send_to_rtdm_service.evaluate()
        if not result:
            return result

        # Проверяем результат и запускаем задачу на периодическую проверку.
        return self.check_scoring_result()

    def send_client_refused(self):
        """Отправка отказа клиента """
        NotImplementedError()

    def send_client_approve_ci(self):
        """ Отправка подтверждения клиента на проверку через БКИ """
        NotImplementedError()

    def send_agreement(self):
        """ Отправка запроса на выбор данного кредитного продукта клиентом """
        NotImplementedError()

    def send_documents(self):
        """ Отправить сканы подписанных документов """
        NotImplementedError()

    def send_authorization(self):
        """ Отправить подтверждение клиента о взятии кредита """
        check_score_result_service = CheckScoreResultService(self.ocp)
        check_score_result_service.evaluate()

    def check_scoring_result(self):
        """Выполняется раз в 5 секунд - запрос на проверку результатов скоринга"""
        check_score_result_service = CheckScoreResultService(self.ocp)
        result = check_score_result_service.evaluate()

        if not result:
            from .updaters.tasks import check_order_status
            check_order_status.send_with_options(args=(self.ocp.id), delay=5000)

