from django.test import TestCase

from ...mts.forms.register_req_middle import RegisterReqMiddleBankForm
from ...const import BankBrand
from ..base_test_case import BaseBankFormMixin
from ..forms import CreateFormMixin


class RegisterReqMiddleTestCase(CreateFormMixin, BaseBankFormMixin, TestCase):
    bank_name = BankBrand.MTS
    bank_form = RegisterReqMiddleBankForm
