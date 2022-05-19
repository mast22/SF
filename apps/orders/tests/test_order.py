from decimal import Decimal

from django.core.exceptions import ValidationError

from apps.banks.const import BankBrand
from apps.banks.models import CreditProduct, Bank
from banks.tests.banks.base_test_case import BaseBankFormMixin
from apps.common.exceptions import BadStateException
from apps.orders.checks import check_all_order_objects_defined, check_initial_payment_is_less_than_purchase_amount
from apps.orders.models import Order, OrderHistory, OrderCreditProduct
from apps.orders.const import OrderStatus, CreditProductStatus
from apps.testing.fixtures.all_data import create_fixtures
from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase, APIClient

from apps.testing.fixtures.pieces.bank_products import create_credit_product
from apps.users.const import Roles
from apps.users.models import User


class OrderTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_fixtures(['banks', 'full_order'])
        cls.order = Order.objects.first()

    def setUp(self):
        self.order.refresh_from_db()

    def test_change_status_through_fsm(self):
        """ Тест покрывает добавление статуса в `Order.change_status_history()`,
        вызываемый в `save()` и `store_new_status()` в workflows
        """
        self.order.set_client_refused()

        new: OrderHistory = self.order.history.first()
        client_refused: OrderHistory = self.order.history.last()

        self.assertEqual(new.order_status, OrderStatus.NEW)
        self.assertEqual(client_refused.order_status, OrderStatus.CLIENT_REFUSED)

    def test_change_status_to_scoring(self):
        self.order.set_scoring()
        self.assertEqual(self.order.status, OrderStatus.SCORING)


class HasEverBeenScored(BaseBankFormMixin, TestCase):
    bank_name = BankBrand.OTP

    def setUp(self):
        super(HasEverBeenScored, self).setUp()
        self.ocp.delete()

    def test_has_ever_been_scored_not_ocp(self):
        self.assertFalse(self.order.has_ever_been_scored())

    def test_has_ever_been_scored_only_not_sent(self):
        OrderCreditProduct.objects.create(
            credit_product=self.credit_product,
            order=self.order,
            status=CreditProductStatus.NOT_SENT
        )

        self.assertFalse(self.order.has_ever_been_scored())

    def test_has_ever_been_scored_in_process(self):
        OrderCreditProduct.objects.create(
            credit_product=self.credit_product,
            order=self.order,
            status=CreditProductStatus.IN_PROCESS
        )

        self.assertTrue(self.order.has_ever_been_scored())

    def test_has_ever_been_scored_not_sent_and_in_process(self):
        bank2 = Bank.objects.create(name=BankBrand.ALFA)
        cp2 = create_credit_product(bank=bank2)
        OrderCreditProduct.objects.create(
            credit_product=self.credit_product,
            order=self.order,
            status=CreditProductStatus.IN_PROCESS
        )
        OrderCreditProduct.objects.create(
            credit_product=cp2,
            order=self.order,
            status=CreditProductStatus.NOT_SENT
        )

        self.assertTrue(self.order.has_ever_been_scored())


class OrderChecksTestCase(BaseBankFormMixin, TestCase):
    """ Тестирование проверок, проводимых перед отправкой на скоринг """
    bank_name = BankBrand.OTP

    def test_all_steps_completed(self):
        try:
            check_all_order_objects_defined(self.order)
        except Exception:
            self.fail()

    def test_not_all_steps_completed(self):
        self.order.passport.delete()

        self.assertRaises(BadStateException, check_all_order_objects_defined, self.order)


    def test_check_initial_payment_is_more_than_purchase_amount(self):
        # Сделаем их равными чтобы вызвать исключение
        purchase_amount = self.order.purchase_amount
        credit = self.order.credit
        credit.initial_payment = purchase_amount
        credit.save()

        self.assertRaises(BadStateException, check_initial_payment_is_less_than_purchase_amount, self.order)

    def test_check_initial_payment_is_less_than_purchase_amount(self):
        self.order.purchase_amount = self.order.credit.initial_payment * 2 # Удостоверимся, что размер заказа больше
        self.order.save()
        self.assertGreater(self.order.purchase_amount, self.order.credit.initial_payment)

        try:
            check_initial_payment_is_less_than_purchase_amount(self.order)
        except BadStateException:
            self.fail()



class OrderAPITestCase(APITestCase):
    def setUp(self):
        create_fixtures(['banks', 'full_order'])
        self.order = Order.objects.first()
        self.agent = User.objects.filter(role=Roles.AGENT).first()
        self.client = APIClient()

    def make_personal_data_meta_field_patch(self):
        personal_data_id = self.order.personal_data.id
        personal_data_url = reverse('api:personaldata-detail', args=[personal_data_id])
        data = {
            "data": {
                "id": personal_data_id,
                "type": "personal-data",
                "meta": {"full_name": "Сергей2"}
            }
        }
        self.client.force_login(user=self.agent)
        return self.client.patch(personal_data_url, data=data)

    def test_change_meta_fields_has_no_effect(self):
        """ При изменении meta_fields поля ошибка не поднимается """
        response = self.make_personal_data_meta_field_patch()
        self.assertEqual(response.status_code, 200, response.json())


class OrderUniqueBankForEveryOCPTestCase(TestCase):
    def setUp(self):
        create_fixtures(['banks', 'full_order'])
        self.order = Order.objects.first()

    def test_create_ocps_with_different_banks(self):
        self.order.order_credit_products.all().delete()
        otp_cp = CreditProduct.objects.filter(bank__name=BankBrand.OTP).first()
        alfa_cp = CreditProduct.objects.filter(bank__name=BankBrand.ALFA).first()

        OrderCreditProduct.objects.create(credit_product=otp_cp, order=self.order)
        OrderCreditProduct.objects.create(credit_product=alfa_cp, order=self.order)

    def test_create_ocps_with_same_banks(self):
        self.order.order_credit_products.all().delete()
        otp_cp = CreditProduct.objects.filter(bank__name=BankBrand.OTP).first()

        OrderCreditProduct.objects.create(credit_product=otp_cp, order=self.order)
        with self.assertRaises(ValidationError):
            OrderCreditProduct.objects.create(credit_product=otp_cp, order=self.order)

    def test_update_ocps_does_not_raise_error(self):
        self.order.order_credit_products.all().delete()
        otp_cp = CreditProduct.objects.filter(bank__name=BankBrand.OTP).first()

        ocp = OrderCreditProduct.objects.create(credit_product=otp_cp, order=self.order)
        try:
            ocp.update_with_status(CreditProductStatus.TECHNICAL_ERROR)
        except ValidationError:
            self.fail('Обновление не должно поднимать ошибку')


class UpdateWithStatusTestCase(BaseBankFormMixin, TestCase):
    """ update_with_status_правильно обновляет статусы """
    bank_name = BankBrand.OTP

    def test_first_scoring_result(self):
        """ Приходит первый ответ от банка, мы переводим статус заказа в SELECTION """
        # Немножко читерим и устанавливаем статус системы в необходимы нам вид
        self.order.status = OrderStatus.SCORING
        self.order.save()
        self.ocp.status = CreditProductStatus.IN_PROCESS
        self.ocp.save()

        self.ocp.update_with_status(CreditProductStatus.SUCCESS)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, OrderStatus.SELECTION)

    def test_first_scoring_result_already_selection(self):
        self.order.status = OrderStatus.SELECTION
        self.order.save()
        self.ocp.status = CreditProductStatus.IN_PROCESS
        self.ocp.save()

        self.ocp.update_with_status(CreditProductStatus.SUCCESS)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, OrderStatus.SELECTION)

    def test_reject_single_ocp(self):
        # Если у нас была только 1 отправка, то изначальный статус - SCORING,
        # И по сути мы должны на этом закончить, один единственный отклонен - все отклонены
        self.order.status = OrderStatus.SCORING
        self.order.save()
        self.ocp.update_with_status(CreditProductStatus.REJECTED)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, OrderStatus.REJECTED)

    def test_do_not_reject_if_single_ocp_was_rejected(self):
        self.order.status = OrderStatus.SCORING
        self.order.save()
        alfa_cp = CreditProduct.objects.create(
            bank=Bank.objects.create(name=BankBrand.ALFA),
            total_max=Decimal(100),
            total_min=Decimal(50),
            initial_payment_min=Decimal(100),
            initial_payment_max=Decimal(1000),
            term_min=3,
            term_max=12,
            annual_rate=Decimal(5),
        )
        self.ocp2 = OrderCreditProduct.objects.create(credit_product=alfa_cp, order=self.order)

        self.ocp2.update_with_status(CreditProductStatus.SUCCESS)
        self.ocp.update_with_status(CreditProductStatus.REJECTED)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, OrderStatus.SELECTION)


class CloneOrderTestCase(BaseBankFormMixin, APITestCase):
    bank_name = BankBrand.OTP
    client = APIClient()

    @staticmethod
    def get_url(order_id):
        return f'/api/orders/{order_id}/clone_order/'

    def test_clone_order(self):
        self.ocp.status = CreditProductStatus.IN_PROCESS
        self.ocp.save()
        self.client.force_login(user=self.agent)
        response = self.client.get(self.get_url(self.order.id))
        self.assertEqual(response.status_code, 201, response.json())

    def test_clone_not_sent_order(self):
        self.client.force_login(user=self.agent)
        response = self.client.get(self.get_url(self.order.id))
        self.assertEqual(response.status_code, 409, response.json())


class SetOrderToNewTestCase(BaseBankFormMixin, APITestCase):
    bank_name = BankBrand.OTP
    client = APIClient()

    def test_order_reset_to_new(self):
        self.order