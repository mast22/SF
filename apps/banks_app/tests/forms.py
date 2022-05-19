import logging
from decimal import Decimal
from typing import Optional

from apps.banks_app.base.service import BaseService
from apps.banks.utils import create_soap_xml

from apps.orders.const import WorkplaceCategory, MaritalStatus

logger = logging.getLogger('testing')


class BaseFormConversionMixin:
    """ Класс описывает вариации данных, которые могут направлены в банк """
    service: Optional[BaseService] = None

    def test_form_conversion(self):
        """ Конвертация полностью заполненного заказа """
        result = self.form.convert_order_to_bank_payload()
        self.assertTrue(isinstance(result, dict))  # Проверим что мы получили результат

        if self.service is not None:
            logger.info("Method %s, result %s", self.service.method, result)
            xml = create_soap_xml(self.service.wsdl_file, self.service.method, result)
            self.assertTrue(bool(xml))  # Проверим что мы получили результат
            logger.info("XML %s", xml.decode('utf-8'))


class CreateFormMixin(BaseFormConversionMixin):
    """ Следует использовать для тестирования анкеты (формы) в которой отправляется данные клиента """

    def test_unemployed_conversion(self):
        """ Проверяет работоспособность формы при безработном клиенте """
        ce = self.order.career_education
        ce.workplace_category = WorkplaceCategory.UNEMPLOYED
        ce.is_student = False
        ce.worker_status = None
        ce.position_type = None
        ce.retiree_status = None
        ce.monthly_income = Decimal(100000)
        ce.monthly_expenses = Decimal(50000)
        ce.org_name = None
        ce.org_industry = None
        ce.position = None
        ce.org_ownership = None
        ce.months_of_exp = None
        ce.org_location = None
        ce.job_phone = None
        ce.save()

        result = self.form.convert_order_to_bank_payload()
        self.assertTrue(isinstance(result, dict))

    def test_create_sequence_with_single(self):
        """ Проверка появления известного бага при отправке пользователя с социальным статусов "одинок" Sadge """
        fd = self.order.family_data
        fd.marital_status = MaritalStatus.SINGLE
        fd.marriage_date = None
        fd.partner_first_name = None
        fd.partner_last_name = None
        fd.partner_middle_name = None
        fd.partner_is_student = None
        fd.partner_worker_status = None
        fd.partner_retiree_status = None
        fd.save()

        result = self.form.convert_order_to_bank_payload()
        self.assertTrue(isinstance(result, dict))
