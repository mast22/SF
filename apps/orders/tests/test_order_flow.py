from unittest import skipIf

from django.test import override_settings
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase, APIClient

from apps.banks.const import BankBrand
from banks.tests.banks.base_test_case import BaseBankFormMixin
from apps.orders.const import OrderStatus, CreditProductStatus
from apps.orders.models import Order, Client
from apps.testing.fixtures.all_data import create_fixtures
from apps.testing.fixtures.pieces.order import create_order_flow_objects
from apps.users.const import Roles
from apps.users.models import User


class UpdateOrderStepsTestCase(APITestCase):
    """ Заказ запрещено изменять если он находится на этапе создания """
    client = APIClient()

    def setUp(self):
        create_fixtures(['banks', 'full_order'])
        self.order: Order = Order.objects.first()
        self.agent = User.objects.filter(role=Roles.AGENT).first()

    def make_personal_data_patch(self):
        personal_data_id = self.order.personal_data.id
        personal_data_url = reverse('api:personaldata-detail', args=[personal_data_id])
        data = {
            "data": {
                "id": personal_data_id,
                "type": "personal-data",
                "attributes": {"first_name": "Сергей", }
            }
        }
        self.client.force_login(user=self.agent)
        return self.client.patch(personal_data_url, data=data, format='vnd.api+json')

    def test_client_data_modifiable(self):
        """ Пока у заказа статус "new" данные клиентов можно изменять """
        response = self.make_personal_data_patch()
        self.assertEqual(response.status_code, 200, response.json())

    def test_client_is_not_modifiable(self):
        self.order.set_client_refused()
        self.order.save()
        response = self.make_personal_data_patch()
        self.assertEqual(response.status_code, 409, response.json())


@skipIf(True, "Skipping step only test")
@override_settings(USE_TESTING_BANK_CREDS=True, CALCULATE_OPERATIONAL_DATA=False)
class OrderFlowTestCase(BaseBankFormMixin, APITestCase):
    """ Процесс создания заказа описанный в форме обращения в API

    Тест для прохождения в дебаг режиме и осмотра выполнения программного кода.
    Он проваливается поскольку сразу после отправки на скоринг происходит запрос на документы.
    Документы не придут так как скоринг ещё не завершился

    Также может не работать поскольку ОТП не всегда принимает запросы
    """
    bank_name = BankBrand.OTP
    api_client = APIClient()
    client_list_url = reverse('api:client-list')
    client_order_list_url = reverse('api:clientorder-list')
    order_list_url = reverse('api:order-list')
    documents_to_sign_list_url = reverse('api:documenttosign-list')
    new_client_phone = "+79991454323"

    def get_order_detail_url(self, order_id):
        return reverse('api:order-detail', args=(order_id,))

    def setUp(self):
        super(OrderFlowTestCase, self).setUp()
        self.outlet = self.order.outlet
        # Выставим заказ в статус нового чтобы начать по нему работу
        self.credit_product = self.ocp.credit_product
        self.order.delete()

    def create_client(self):
        client_payload = {
            "data": {
                "type": "clients",
                "attributes": {
                    "phone": self.new_client_phone
                },
            }
        }
        return self.api_client.post(self.client_list_url, client_payload)

    def create_client_order(self, client_id):
        client_order_payload = {
            "data": {
                "type": "client-orders",
                "relationships": {
                    "client": {"data": {"id": client_id, "type": "clients"}}
                }
            }
        }
        return self.api_client.post(self.client_order_list_url, client_order_payload)

    def create_order(self, client_order_id):
        order_payload = {
            "data": {
                "type": "orders",
                "relationships": {
                    "client_order": {"data": {"id": client_order_id, "type": "client-orders"}},
                    "agent": {"data": {"id": self.agent.id, "type": "agents"}},
                    "outlet": {"data": {"id": self.outlet.id, "type": "outlets"}}
                }
            }
        }
        return self.api_client.post(self.order_list_url, order_payload)

    def send_order_to_scoring(self, order_id):
        return self.api_client.post(self.get_order_detail_url(order_id) + 'send_to_scoring/')

    def fill_in_order(self, order_id):
        create_order_flow_objects(self.client, self.order, self.agent, self.outlet)

    def choose_credit_product(self, ocp_id: int):
        url = self.get_order_detail_url(self.order.id) + 'choose_credit_product/'
        payload = {'chosen_product': ocp_id}

        return self.api_client.post(url, payload, format='json')

    def prepare_order(self):
        """ Подготовка заказа к отправке, это финальная форма, которая доступна к отправке """
        # Допустим клиента не нашли, тогда создадим нового
        resp1 = self.create_client()
        self.assertEqual(resp1.status_code, 201, msg=f'create_client. Resp: {resp1.json()}')
        client_id = resp1.json()['data']['id']
        self.client = Client.objects.get(id=client_id)

        # Теперь нужно создать клиента в заказе:
        resp2 = self.create_client_order(client_id)
        self.assertEqual(resp2.status_code, 201, msg=f'create_client. Resp: {resp2.json()}')

        # И создадим заказ
        resp3 = self.create_order(resp2.json()['data']['id'])
        self.assertEqual(resp3.status_code, 201, f'create_order. Resp: {resp3.json()}')
        order_id = resp3.json()['data']['id']
        self.order = Order.objects.get(id=order_id)

        self.order.credit_products.set([self.credit_product])

        # Заполняем данными заказ
        self.fill_in_order(order_id)

    def test_create_sequence(self):
        """ Пустой заказ - тот, который не из телеграмма """

        self.api_client.force_login(user=self.agent)
        self.prepare_order()

        response = self.send_order_to_scoring(self.order.id)
        self.assertEqual(response.status_code, 202)

        self.order.refresh_from_db()
        self.ocp.refresh_from_db()
        self.assertEqual(self.order.status, OrderStatus.SCORING, self.ocp.bank_data)

        ocp = self.order.order_credit_products.first()
        self.assertEqual(ocp.status, CreditProductStatus.IN_PROCESS, ocp.bank_data)

        # Мы не получаем колбек локально, поэтому просто отмечает что скоринг прошёл
        ocp.status = CreditProductStatus.SUCCESS  # Проходим скоринг
        ocp.save()
        self.choose_credit_product(ocp.id)
        # Клиент получает документы для подписания по web socket
        # На данный момент просто происходит долгий запрос

        # Должны появиться документы для клиента
        resp6 = self.api_client.get(self.documents_to_sign_list_url)
        self.assertGreater(resp6.json()['meta']['pagination']['count'], 0, ocp.bank_data)
