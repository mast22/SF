from .const import BankPriorityChoice



def set_order_credit_prioriy(order_credit_product):
    bank = order_credit_product.credit_product.bank
    # TODO: Написать расчёт приоритетов для конкретного кредитного продукта!
    priority = BankPriorityChoice.FIRST
    return priority
