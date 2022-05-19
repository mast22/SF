from apps.banks import logger
from apps.common.transitions import change_state
from apps.orders_ws.shortcuts import send_message_sync, WSMessageType
from ..base.provider import BaseBankProvider
from ..base.exceptions import FaultyRequestException
from .const import OTP_SCORING_DECISIONS
from .services import (
    ClientRefusedService,
    CreateAgreementService,
    ScoringService,
    SendAuthorizationService,
    SendDocumentsService
)


class OTPBankProvider(BaseBankProvider):
    """ Бизнес логика обработки запросов ОТП банка """

    def send_to_scoring(self):
        self.process_sending_to_scoring()
        service = ScoringService(self.ocp)

        try:
            service.evaluate()
        except FaultyRequestException:
            self.process_network_callback()

    def send_client_refused(self):
        service = ClientRefusedService(self.ocp)
        service.evaluate()

    def send_agreement(self):
        service = CreateAgreementService(self.ocp)
        service.evaluate()

    def send_documents(self):
        """ Отправка подписанного договора  """
        send_docs_service = SendDocumentsService(self.ocp)
        send_docs_service.evaluate()

        send_auth_service = SendAuthorizationService(self.ocp)
        send_auth_service.evaluate()

    def send_authorization(self):
        # FIXME авторизация отправляется дважды
        service = SendAuthorizationService(self.ocp)
        service.evaluate()

    def process_scoring_callback(self, data):
        """ Обработка callback-а после получения решения от банка """
        decision_status = OTP_SCORING_DECISIONS[str(data.decision)]
        self.ocp.update_with_status(decision_status)
        logger.info(f'{self.bank.name} scoring callback: {data} for request: order: {self.ocp.order}, ocp: {self.ocp}')

        # В любом случе при приходе ответа от банка мы должны оповестить агента
        # О пришедшем результате
        self.ocp.refresh_from_db()

        send_message_sync(
            self.order.agent_id, self.order.id,
            type=WSMessageType.SCORING_RESULT,
            data=dict(
                order_credit_product=self.ocp.id,
                credit_product=self.ocp.credit_product_id,
                scoring_status=self.ocp.status
            )
        )

    def process_agreement_callback(self, data) -> None:
        """ Обработка callback-а о подтверждении согласия.
        Необходимо сохранить результат и уведомить агентов о статусе авторизации
        """

        # TODO оповестить с каким именно документов проблема
        # TODO добавить оповещение о принятии документа

        # У этого метода только 2 статуса
        if int(data.CheckResult) == 1:
            change_state(self.order.set_authorized, 'Ошибка при авторизации договора')
            self.order.save()

            send_message_sync(
                self.order.agent_id, self.order.id,
                type=WSMessageType.AGREEMENT_ACCEPTED,
                data=dict(
                    status=self.order.status,
                    contract=self.order.contract.id,
                )
            )

            return

        elif int(data.CheckResult) == 2:
            change_state(self.order.set_documents_error, 'Ошибка при установке требования о доработке сканов')
            self.order.save()

            send_message_sync(
                self.order.agent_id, self.order.id,
                type=WSMessageType.AGREEMENT_REJECTED,
                data=dict(
                    status=self.order.status,
                    contract=self.order.contract.id,
                )
            )

            return

    def process_sending_to_scoring(self):
        """ Отправка оповещения клиенту после отправки заявки на скоринг """
        send_message_sync(
            self.order.agent_id, self.order.id,
            type=WSMessageType.SENDING_TO_SCORING,
            data=dict(
                order_credit_product=self.ocp.id,
                bank=self.bank.name
            )
        )

    def process_network_callback(self) -> None:
        send_message_sync(
            self.order.agent_id, self.order.id,
            type=WSMessageType.REQUEST_ERROR,
            data=dict(
                order_credit_product=self.ocp.id,
            )
        )
