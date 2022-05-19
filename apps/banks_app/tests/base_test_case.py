from typing import Optional, Type

from apps.banks_app.base.forms import BaseBankForm
from apps.banks.const import BankBrand
from apps.testing.fixtures.bank_testing_fixtures import set_up_fixture


class BaseBankFormMixin:
    bank_form: Optional[Type[BaseBankForm]] = None
    bank_name = BankBrand.OTP

    def setUp(self):
        self.ocp, self.credit_product, self.order, self.bank, self.agent, self.ter_man = set_up_fixture(self.bank_name)
        if self.bank_form is not None:
            self.form = self.bank_form(self.ocp, self.order, self.bank, self.credit_product)
