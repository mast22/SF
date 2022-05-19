from unittest import TestCase
from django.test import TestCase as DjangoTestCase

from apps.banks_app.base.forms import BaseBankForm
from apps.banks_app.base.rules import RawRule, MethodRule, ConstRule, TransformRule, EnumRule, CalculatedRule, \
    AccordanceRule, LoopRule, DictRule
from apps.banks.const import BankBrand
from apps.banks.models import Bank, CreditProduct
from .base_test_case import BaseBankFormMixin
from apps.orders.models import Order, OrderCreditProduct, Passport


class RuleTestCaseForm(BaseBankForm):
    mapper = {
        'raw_rule': RawRule('passport.first_name'),
        'method_rule': MethodRule('method'),
        'const_rule': ConstRule('value'),
        'transform_rule': TransformRule('passport.first_name', lambda value: value.upper()),
        'enum_rule': EnumRule('passport.first_name', {'first_name': 'right_answer', 'last_name': 'wrong'}),
        'calculated_rule': CalculatedRule(lambda base: base.passport.first_name),
        'const_rule_not_proceed': ConstRule('value').with_proceed(lambda _: False),
        'const_rule_not_present': ConstRule('value').with_presence(lambda _: False),
        'dict_rule': DictRule(
            data={
                'const_rule': ConstRule('Hello')
            }
        )
    }

    def method(self):
        return 'method_result'


class SimpleRulesTestCase(TestCase):
    """ Проверяем результат выполнения простых правил """

    def setUp(self) -> None:
        self.order = Order()
        self.ocp = OrderCreditProduct()
        self.bank = Bank()
        self.credit_product = CreditProduct()

        self.passport = Passport()
        self.passport.first_name = 'first_name'
        self.order.passport = self.passport

    def test_right_result(self):
        expected_result = {}
        expected_result['raw_rule'] = self.passport.first_name
        expected_result['method_rule'] = 'method_result'
        expected_result['const_rule'] = 'value'
        expected_result['transform_rule'] = 'FIRST_NAME'
        expected_result['enum_rule'] = 'right_answer'
        expected_result['calculated_rule'] = 'first_name'
        expected_result['dict_rule'] = {'const_rule': 'Hello'}

        form = RuleTestCaseForm(order=self.order, ocp=self.ocp, credit_product=self.credit_product, bank=self.bank)
        result = form.convert_order_to_bank_payload()
        self.assertEqual(expected_result, result)


class AccordanceRuleTestCaseForm(BaseBankForm):
    mapper = {
        'accordance': AccordanceRule('career_education.org_industry'),
        # TODO написать тест AccordanceRule в LoopRule
    }


class AccordanceRuleTestCaseFormWithMultipleValues(BaseBankForm):
    mapper = {
        'accordance': AccordanceRule(
            'career_education.org_industry',
            func=lambda x: x[0]
        ),
    }


class AccordanceRuleTestCase(BaseBankFormMixin, DjangoTestCase):
    def test_accordance_rule(self):
        form = AccordanceRuleTestCaseForm(
            order=self.order, ocp=self.ocp, credit_product=self.ocp.credit_product, bank=self.bank
        )
        result = form.convert_order_to_bank_payload()
        self.assertIsInstance(result['accordance'], str, result['accordance'])
        result['accordance'] = self.order.career_education.org_industry.specific[self.bank.name]

    def test_multiple_value_in(self):
        # некоторые банки требуют несколько значений для обозначения одного например 1 категории
        industry = self.order.career_education.org_industry
        new_specific = industry.specific
        new_specific[BankBrand.OTP] = [345, 'Agriculture']
        industry.specific = new_specific
        industry.save()

        form = AccordanceRuleTestCaseFormWithMultipleValues(
            order=self.order, ocp=self.ocp, credit_product=self.ocp.credit_product, bank=self.bank
        )
        result = form.convert_order_to_bank_payload()
        self.assertEqual(result['accordance'], 345)


class LoopRuleTestCaseBankForm(BaseBankForm):
    mapper = {
        'loop_rule': LoopRule(
            lookup='goods',
            children_name='Good',
            inner={
                'name': ConstRule('Name')
            },
        )
    }


class LoopRuleTestCase(BaseBankFormMixin, DjangoTestCase):
    def test_loop_rule(self):
        form = LoopRuleTestCaseBankForm(
            order=self.order, ocp=self.ocp, credit_product=self.ocp.credit_product, bank=self.bank
        )
        result = form.convert_order_to_bank_payload()

        self.assertEqual(result, {'loop_rule': {'Good': [{'name': 'Name'} for i in range(form.order.goods.count())]}})
