from typing import Dict

from django.urls import reverse

from banks.tests.banks.base_test_case import BaseBankFormMixin
from apps.misc.const import AccordanceCollection
from apps.misc.models import Accordance
from apps.orders.models import OrderGood, Good, Order, ClientOrder
from rest_framework.test import APITestCase, APIClient

from apps.testing.fixtures.bank_testing_fixtures import set_up_fixture


class OrderGoodSignalTestCase(BaseBankFormMixin, APITestCase):
    api_client = APIClient()

    def setUp(self):
        self.ocp, self.credit_product, self.old_order, self.bank, self.agent, self.ter_man = set_up_fixture(self.bank_name)
        self.client = self.old_order.client_order.client
        self.outlet = self.old_order.outlet
        self.client_order = ClientOrder.objects.create(
            client=self.client,
            phone=self.client.phone,
        )
        Accordance.objects.create(
            desc="test",
            general="test",
            specific={"123": "asd"},
            collection=AccordanceCollection.GOOD_CATEGORY
        )

    def make_request(self, payload: Dict):
        self.api_client.force_login(self.agent)
        response = self.api_client.post(reverse("api:order-list"), payload)
        self.assertEqual(response.status_code, 201, response.json())
        self.order = Order.objects.get(id=response.json()["data"]["id"])

        return response

    def test_create_order_with_products(self):
        payload = {
            "data": {
                "type": "orders",
                "attributes": {
                    "purchase_amount": 0,
                },
                "relationships": {
                    "client_order": {"data": {"id": self.client_order.id, "type": "client-orders"}},
                    "agent": {"data": {"id": self.agent.id, "type": "agents"}},
                    "outlet": {"data": {"id": self.outlet.id, "type": "outlets"}}
                }
            }
        }
        self.make_request(payload)
        self.order.refresh_from_db()
        self.assertEqual(self.order.purchase_amount, 0)
        OrderGood.objects.create(
            good=Good.objects.create(
                brand="Apple",
                model="12X",
                name="Phone",
                category_id=1,
            ),
            order=self.order,
            amount=1,
            price=8000
        )

        self.order.refresh_from_db()
        self.assertEqual(self.order.purchase_amount, 8000)

    def test_create_order_without_products(self):
        pa = 8000.00
        payload = {
            "data": {
                "type": "orders",
                "attributes": {
                    "purchase_amount": pa,
                },
                "relationships": {
                    "client_order": {"data": {"id": self.client_order.id, "type": "client-orders"}},
                    "agent": {"data": {"id": self.agent.id, "type": "agents"}},
                    "outlet": {"data": {"id": self.outlet.id, "type": "outlets"}}
                }
            }
        }

        response = self.make_request(payload)
        self.order.refresh_from_db()

        self.assertEqual(self.order.purchase_amount, pa)
