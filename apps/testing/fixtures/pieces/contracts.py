from apps.deliveries.models import Delivery
from apps.orders.models import Order, Contract
from apps.testing.fixtures.data import get_random_int_string


def create_deliveries(orders):
    delivery_1 = Delivery.objects.create()
    delivery_2 = Delivery.objects.create()

    half_order_length = len(orders) // 2

    orders_1 = Order.objects.filter(id__in=list(map(lambda x: x.id, orders[:half_order_length])))
    orders_2 = Order.objects.filter(id__in=list(map(lambda x: x.id, orders[half_order_length:])))

    contracts = []
    for orders_list, delivery in ((orders_1, delivery_1), (orders_2, delivery_2)):
        for order in orders_list:
            ct = Contract(delivery=delivery, order=order, bank_number=get_random_int_string(10))
            contracts.append(ct)
    Contract.objects.bulk_create(contracts)
