from collections import defaultdict
from apps.common.transitions import change_state
from apps.orders.const import CreditProductStatus
from apps.banks_app import OTPBankProvider, AlphaBankProvider, PochtaBankProvider, MTSBankProvider
from .models import Bank, TerManBank
from .const import BankBrand


BANKS = {
    BankBrand.OTP: OTPBankProvider,
    BankBrand.ALFA: AlphaBankProvider,
    BankBrand.POCHTA: PochtaBankProvider,
    BankBrand.MTS: MTSBankProvider,
}


def send_order_to_agreement(order):
    """Отправка в банк согласия клиента на взятие кредита."""
    ocp = order.chosen_product
    bank = ocp.credit_product.bank
    bank_provider_class = BANKS.get(bank.name, None)
    if not bank_provider_class:
        return None
    bank_provider = bank_provider_class(ocp)
    bank_provider.send_agreement()


def send_order_client_refused(order):
    """ Отправка отказа клиента по кредиту во все банки """
    results = {}
    ocps = order.order_credit_products.all().select_related('credit_product__bank')
    for ocp in ocps:
        result = send_client_refused_exact_bank(ocp)
        results[ocp.id] = result
    return results


def send_order_documents(order):
    """Отправка в банк подписанных клиентом сканов документов."""
    bank = order.chosen_product.credit_product.bank
    bank_provider_class = BANKS.get(bank.name, None)
    if not bank_provider_class:
        return None
    bank_provider = bank_provider_class(bank, order)
    bank_provider.send_documents()


def send_order_to_authorization(order):
    """Отправка окончательного подтверждения о взятии кредита."""
    bank = order.chosen_product.credit_product.bank
    bank_provider_class = BANKS.get(bank.name, None)
    if not bank_provider_class:
        return None
    bank_provider = bank_provider_class(bank, order)
    bank_provider.send_authorization()


def send_client_refused_exact_bank(ocp):
    """Отправка отказа клиента по OCP """
    bank_provider_class = BANKS.get(ocp.credit_product.bank.name, None)
    bank_provider = bank_provider_class(ocp)
    bank_resp = bank_provider.send_client_refused()
    return bank_resp


# def get_bank_product(resp):
#     from apps.orders.models import OrderCreditProduct
#     current_cp = OrderCreditProduct.objects.select_related(
#         'credit_product', 'order').get(bank_id=resp.bank_order)
#     current_cp.status = resp.status
#     current_cp.save()
#     return current_cp


def get_priorities(bank: Bank, order):
    # Выбираем приоритеты банков, по кредитным продуктам которых ещё не пришёл ответ:
    bank_priorities_qs = TerManBank.objects.filter(
        ter_man_id=order.agent.ter_man_id,
        terman_credit_products__credit_products__order_credit_products__order=order,
        terman_credit_products__credit_products__order_credit_products__status=CreditProductStatus.IN_PROCESS,
    ).order_by('priority').select_related('bank')
    current_bp = None
    bank_priorities = defaultdict(list)
    for bp in bank_priorities_qs:
        bank_priorities[bp.priority].append(bp.bank)
        if bp.bank_id == bank.id:
            # Найден приоритет текущего банка
            current_bp = bp.priority
    if current_bp is None:
        raise AttributeError(f'Something is wrong, there is no priority for bank {bank} in: {bank_priorities}!')
    return current_bp, bank_priorities


def process_order_statuses(resp, order, bank, current_cp):
    """Непосредственно работа над статусами заказа."""
    from apps.orders.models import OrderCreditProduct
    # У нас есть список банков, упорядоченный по приоритетам И есть приоритет текущего банка.
    if current_cp.status == CreditProductStatus.REJECTED:
        # Если ответ банка - негативный, нужно посмотреть, остались ли ещё банки без ответа
        empty_results_exists = OrderCreditProduct.objects.filter(
            order_id=order.id, status=CreditProductStatus.IN_PROCESS
        ).exists()
        if not empty_results_exists:
            # Данный заказ - последний, ставлю заявке статус - "Отказано"
            change_state(order.set_scoring_rejected, None)
            order.save(update_fields=('status',))
        # else:
        #     # Данный ответ - не последний, статус уже был изменён, ничего не делаем.
        #     pass
    # else:
    #     # Если ответ положительный или предварительно-позитивный:
    #     # Нужно понять, пришли ли уже ответы от банков с более высоким приоритетом
    #     # Смотрим на статус заказа:
    #     if order.status == OrderStatus.SCORING:
    #         # Если статус "скоринг", наш ответ - первый или один из промежуточных.
    #         # Нужно найти, какой у нашего банка приоритет среди ещё не ответивших банков.
    #         current_bp_is_max = get_priorities(bank, order)
    #         if current_bp_is_max:
    #             # Если приоритет - наивысший, то меняем статус заказу, если нет - не меняем.
    #             change_state(order.set_successful, None)
    #             order.save(update_fields=('status',))
    #         else:
    #             # Иначе - ничего не делаем с заказом.
    #             pass
    #     else:
    #         # Если статус уже изменён, то уже пришёл ответ от банка с таким же или более высоким приоритетом.
    #         # Ничего не делаем.
    #         pass
