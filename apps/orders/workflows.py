import logging
from apps.common.transitions import StateMachineMixinBase
from apps.common.exceptions import BadStateException
from .checks import check_all_order_objects_defined, check_initial_payment_is_less_than_purchase_amount
from .const import OrderStatus


class OrderStatusFSM(StateMachineMixinBase):
    """ Workflow используется для правильного переключения статусов системы

    Чтобы не перепутать порядок выполнения определенных работ. Некоторые статусы выполняют бизнес логику
    они запускают выполнение определенной задачи, допустим сервиса.

    Использование FSM может быть излишне и оно добавляет ненужную трудность, но всё равно является
    отличным способом вызова сервисов чтобы не связываться с их логикой и логикой провайдеров
    """
    model_attribute = 'status'
    states = OrderStatus.keys()
    extra_args = {
        'after_state_change': 'store_new_status',
        'send_event': True,
    }
    transitions = [
        {
            # Клиент может отказаться от кредита в любой момент
            # Кроме когда заказ завершен или клиент отказался
            # Данной транзицией клиент отказывается от услуг всех банков
            'trigger': 'set_client_refused',
            'source': [
                OrderStatus.NEW,
                OrderStatus.TELEGRAM,
                OrderStatus.SCORING,
                OrderStatus.REJECTED,
                OrderStatus.SELECTION,
                OrderStatus.DOCUMENTS_CREATION,
                OrderStatus.DOCUMENTS_SIGNING,
                OrderStatus.DOCUMENTS_ERROR,
                OrderStatus.AUTHORIZATION,
                OrderStatus.AUTHORIZED,
                OrderStatus.UNAUTHORIZED,
            ],
            'dest': OrderStatus.CLIENT_REFUSED,
            'after': 'on_set_order_client_refused',
        },
        {
            # Можно пометить заявку как новую после того, как агент заберёт её себе.
            'trigger': 'set_new',
            'source': [
                OrderStatus.TELEGRAM,
            ],
            'dest': OrderStatus.NEW
        },
        {
            # Отправка на скоринг
            'trigger': 'set_scoring',
            'source': [OrderStatus.NEW],
            'dest': OrderStatus.SCORING,
            'after': 'on_set_order_scoring',
            'before': 'check_order_is_valid'
        },
        {
            # Отказ банков по заказу.
            'trigger': 'set_scoring_rejected',
            'source': [OrderStatus.SCORING],
            'dest': OrderStatus.REJECTED,
        },
        {
            # Меняем статус когда приходит первый положительный ответ от банка, можем переходить к выбору продукта
            'trigger': 'set_selection',
            'source': [OrderStatus.SCORING],
            'dest': OrderStatus.SELECTION,
        },
        {
            # Выбор конкретного кредитного продукта
            'trigger': 'set_agreement',
            'source': [OrderStatus.SCORING, OrderStatus.SELECTION],
            'dest': OrderStatus.AGREEMENT,
            'after': 'on_set_order_agreement',
        },
        {
            'trigger': 'set_documents_creation',
            'source': [OrderStatus.AGREEMENT],
            'dest': OrderStatus.DOCUMENTS_CREATION,
        },
        {
            'trigger': 'set_documents_signing',
            'source': [OrderStatus.DOCUMENTS_CREATION],
            'dest': OrderStatus.DOCUMENTS_SIGNING,
        },
        {
            'trigger': 'set_agreement_error',
            'source': [OrderStatus.DOCUMENTS_CREATION],
            'dest': OrderStatus.AGREEMENT_ERROR,
        },
        {
            # Можно начать заявку заново если она ещё не завершена или от неё не отказались
            'trigger': 'reset_new',
            'source': [
                OrderStatus.SCORING,
                OrderStatus.REJECTED,
                OrderStatus.SELECTION,
                OrderStatus.DOCUMENTS_CREATION,
                OrderStatus.DOCUMENTS_SIGNING,
            ],
            'dest': OrderStatus.NEW,
            'after': 'on_reset_order_to_new',
        },
        {
            'trigger': 'set_documents_sending',
            'source': [OrderStatus.DOCUMENTS_SIGNING],
            'dest': OrderStatus.DOCUMENTS_SENDING,
            'after': 'on_set_order_documents_sending',
        },
        {
            # Установка контракта и отправка в банк на авторизацию
            'trigger': 'set_authorization',
            'source': [OrderStatus.DOCUMENTS_SIGNING],
            'dest': OrderStatus.AUTHORIZATION,
            'after': 'on_set_order_authorization',
        },
        {
            'trigger': 'set_authorized',
            'source': [OrderStatus.AUTHORIZATION],
            'dest': OrderStatus.AUTHORIZED,
        },
        {
            'trigger': 'set_unauthorized',
            'source': [OrderStatus.UNAUTHORIZED],
            'dest': OrderStatus.UNAUTHORIZED,
        },
    ]

    @staticmethod
    def store_new_status(event):
        # TODO нужен тест
        if event.error is not None:
            logging.error(f'Error occurred during status change {event.error} of {event.model}')
            return
        order = event.model
        order.change_status_history(event.transition.dest)

    def on_set_order_client_refused(self, event_data):
        from apps.banks import tasks

        tasks.send_order_client_refused.send(self.id)

    def check_order_is_valid(self, event_data):
        check_all_order_objects_defined(self)
        check_initial_payment_is_less_than_purchase_amount(self)

    def on_set_order_scoring(self, event_data):
        from apps.banks import tasks

        tasks.send_order_to_scoring(self)

    def on_set_order_agreement(self, event_data):
        from apps.banks import commission
        from apps.banks import tasks
        chosen_product = event_data.kwargs.get('chosen_product', None)
        if chosen_product is not None:
            self.chosen_product = chosen_product
            self.agent_commission = commission.calculate_agent_commissions_chosen_product(self)
            # self.credit_product_commission_sum, self.extra_services_commission_sum \
            #         = commission.calculate_agent_commissions_chosen_product(self)
            self.save(update_fields=('status', 'chosen_product',))
        elif not self.chosen_product_id:
            raise BadStateException('Chosen product was not set, cant process agreement')

        order_id = self.id

        tasks.send_order_to_agreement.send(order_id)

    def on_set_order_authorization(self, event_data):
        from apps.banks import tasks

        contract = event_data.kwargs.get('contract', None)
        if contract is not None:
            self.contract = contract
            self.save(update_fields=('status', 'contract',))
        elif not self.contract_id:
            raise BadStateException('Contract was not set, cant process authorization')

        order_id = self.id
        tasks.send_order_to_authorization.send(order_id)

    def on_set_order_documents_sending(self, event_data):
        from apps.banks import tasks

        order_id = self.id
        tasks.send_order_documents.send(order_id)

    def on_reset_order_to_new(self, event_data):
        """ Сбрасываем статус заказа на новый """
        self.credit_products.set([])
        self.chosen_product = None

        self.save()
