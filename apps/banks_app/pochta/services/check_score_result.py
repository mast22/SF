from apps.orders_ws.notifiers import notify_scoring_error, notify_scoring_result
from ... import logger
from ...const import CreditProductStatus
from ...base.service import BaseService
from ..forms.check_score_result import CheckScoreResultForm
from ..const import DecisionCode, POCHTA_CREDIT_DECISIONS


class CheckScoreResultService(BaseService):
    wsdl_file = 'apps/banks_app/wsdl/pochta/AfterScoring/BrokerServiceRegistry_25.wsdl'
    form_class = CheckScoreResultForm
    method = 'checkScoreResult'

    def process_before(self):
        self.ocp.update_with_status(CreditProductStatus.IN_PROCESS)

    def process_response(self, data):
        """Получение ответа по скорингку от Почта-банка"""
        if str(data.ErrorCode) != '0':
            logger.debug('Failure')
            self.ocp.update_with_status(CreditProductStatus.TECHNICAL_ERROR, data.ErrorMessage)
            notify_scoring_error(self.ocp, data.ErrorMessage)
            return True

        try:
            decision_code = DecisionCode[data.DecisionCode]
        except Exception as err:
            logger.debug(f'Pochta. CheckScoreResult, otp: {self.ocp}. Wrong data: {data}. Python Error: {err}')
            return True

        if decision_code == DecisionCode.LATER:
            # Решение ещё не принято
            logger.debug(f'Pochta. CheckScoreResult, otp: {self.ocp}, decision is in process')
            return False

        decision_status = POCHTA_CREDIT_DECISIONS[decision_code]
        logger.debug(f'Pochta. CheckScoreResult, otp: {self.ocp}, decision: {decision_code}')
        self.ocp.update_with_status(decision_status, bank_data=data.DecisionComment)
        return True
