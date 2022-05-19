from apps.testing.base import BasePermissionsTestCase
from apps.testing.fixtures.role_testing_fixtures import create
from apps.orders.models import Order, ClientOrder
from typing import Dict, Tuple, List
from django.db.models import Q, Model
from ...api import serializers as s


class OrdersPermissionsTestCase(BasePermissionsTestCase):
    model = Order
    model_fixtures = [create]
    fields_to_check = []
    serializer = s.OrderSerializer
    users = {}
    orders = {}
    outlets = {}
    clients = {}
    extra_services = {}
    credit_products = {}

    @classmethod
    def setup_view_data(cls) -> Tuple[Dict[Model, List], Dict]:
        allowed = {
            cls.users['admin']: [cls.orders['order_1'], cls.orders['order_3']],
            cls.users['acc_man_1']: [cls.orders['order_1']],
            cls.users['acc_man_2']: [cls.orders['order_3']],
            cls.users['ter_man_1']: [cls.orders['order_1']],
            cls.users['ter_man_3']: [cls.orders['order_3']],
            cls.users['agent_1']: [cls.orders['order_1']],
            cls.users['agent_3']: [cls.orders['order_3']],
        }
        forbidden = {
            cls.users['agent_1']: [cls.orders['order_3']],
            cls.users['agent_3']: [cls.orders['order_1']],
            cls.users['agent_2']: [cls.orders['order_1'], cls.orders['order_3']],
            cls.users['ter_man_2']: [cls.orders['order_1'], cls.orders['order_3']], # У агента 2 нет заказов
            cls.users['acc_man_1']: [cls.orders['order_3']],
            cls.users['acc_man_2']: [cls.orders['order_1']],
        }

        return allowed, forbidden

    @classmethod
    def setup_create_data(cls):
        client_order_1 = ClientOrder(phone=cls.clients['client_1'].phone, client=cls.clients['client_1'])
        client_order_2 = ClientOrder(phone=cls.clients['client_1'].phone, client=cls.clients['client_1'])
        client_order_3 = ClientOrder(phone=cls.clients['client_1'].phone, client=cls.clients['client_1'])
        client_order_4 = ClientOrder(phone=cls.clients['client_1'].phone, client=cls.clients['client_1'])
        ClientOrder.objects.bulk_create([client_order_1, client_order_2, client_order_3, client_order_4])

        order_1 = Order(client_order=client_order_1, agent=cls.users['agent_1'], outlet=cls.outlets['outlet1_1'])
        order_2 = Order(client_order=client_order_2, agent=cls.users['agent_1'], outlet=cls.outlets['outlet1_1'])
        order_3 = Order(client_order=client_order_3, agent=cls.users['agent_1'], outlet=cls.outlets['outlet1_1'])
        order_4 = Order(client_order=client_order_4, agent=cls.users['agent_1'], outlet=cls.outlets['outlet1_1'])

        allowed = {
            cls.users['agent_1']: [order_1],
            cls.users['admin']: [order_2],
            cls.users['acc_man_1']: [order_3],
            cls.users['ter_man_1']: [order_4],
        }
        forbidden = {
            cls.users['agent_2']: [order_1],
        }

        return allowed, forbidden

    @classmethod
    def setup_update_data(cls):
        agent_changed = client_changed = outlet_changed = cp_changed = es_changed = cls.orders['order_1']
        agent_changed.agent = cls.users['agent_2']
        client_changed.client = cls.clients['client_3']
        outlet_changed.outlet = cls.outlets['outlet_2']

        # Попытаемся установить агентом cp и es, которые не активны и которые не принадлежат ему
        allowed = {}
        # Изменять поля client_order, outlet, agent запрещено всем,
        # это контролируется в сериалайзере UpdateOrderSerializer
        forbidden = {
            cls.users['admin']: [],
            cls.users['agent_1']: [cls.orders['order_3']],
            cls.users['ter_man_1']: [cls.orders['order_3']],
            cls.users['acc_man_1']: [cls.orders['order_3']],
        }

        return allowed, forbidden
