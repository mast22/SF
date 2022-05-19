from dateutil.relativedelta import relativedelta
from django.test import SimpleTestCase
from datetime import datetime, date, timedelta
from ..api.serializers import PassportSerializer, FamilyDataSerializer, CareerEducationSerializer, \
    PersonalDataSerializer
from rest_framework.validators import ValidationError

from ..api.validators import check_forbidden_words
from ..const import MaritalStatus, WorkplaceCategory


class PassportValidatorTestCase(SimpleTestCase):
    ser = PassportSerializer()

    def test_valid_date(self):
        passport = {
            'birth_date': datetime(1999, 12, 3),
            'receipt_date': datetime(2019, 12, 30),
        }
        self.assertEqual(self.ser.validate(passport), passport)

    def test_invalid_date(self):
        passport = {
            'birth_date': datetime(1999, 12, 3),
            'receipt_date': datetime(2019, 12, 2), # Получил паспорт раньше др
        }
        self.assertRaises(ValidationError, self.ser.validate, passport)

    # Последующие 4 теста практическим аналогичные
    def test_invalid_series(self):
        self.assertRaises(ValidationError, self.ser.validate_series, '55555')

    def test_valid_series(self):
        self.assertEqual(self.ser.validate_series('5555'), '5555')

    def test_invalid_number(self):
        self.assertRaises(ValidationError, self.ser.validate_number, '55555')

    def test_valid_number(self):
        self.assertEqual(self.ser.validate_number('666666'), '666666')

    def test_user_age_is_valid(self):
        now = datetime.now()
        client_bd = now - relativedelta(years=18, days=1)
        self.assertEqual(self.ser.validate_birth_date(client_bd), client_bd)

    def test_user_age_is_invalid(self):
        now = datetime.now()
        client_bd = now - relativedelta(years=17)
        self.assertRaises(ValidationError, self.ser.validate_birth_date, client_bd)


class FamilyDataValidatorTestCase(SimpleTestCase):
    ser = FamilyDataSerializer()

    def test_divorced_has_no_data(self):
        payload = {
            'marital_status': MaritalStatus.DIVORCED,
            'marriage_date': None,
            'partner_first_name': None,
            'partner_last_name': None,
            'partner_middle_name': None,
            'partner_is_student': None,
            'partner_worker_status': None,
            'partner_position_type': None,
            'partner_retiree_status': None,
        }
        self.assertEqual(self.ser.validate(payload), payload)

    def test_partner_can_be_student(self):
        # Cупруг учится
        payload = {
            'marital_status': MaritalStatus.MARRIED,
            'marriage_date': 'set',
            'partner_first_name': 'set',
            'partner_last_name': 'set',
            'partner_middle_name': 'set',
            'partner_is_student': 'set',
            'partner_worker_status': None,
            'partner_position_type': None,
            'partner_retiree_status': None,
        }
        self.assertEqual(self.ser.validate(payload), payload)

    def test_partner_can_be_retired(self):
        # Супруг на пенсии
        payload = {
            'marital_status': MaritalStatus.MARRIED,
            'marriage_date': 'set',
            'partner_first_name': 'set',
            'partner_last_name': 'set',
            'partner_middle_name': 'set',
            'partner_is_student': None,
            'partner_worker_status': None,
            'partner_position_type': None,
            'partner_retiree_status': 'set',
        }
        self.assertEqual(self.ser.validate(payload), payload)

    def test_marital_status_does_not_correspond_fields(self):
        payload = {
            'marital_status': MaritalStatus.MARRIED,
            'marriage_date': None,
            'partner_first_name': None,
            'partner_last_name': None,
            'partner_middle_name': None,
            'partner_is_student': None,
            'partner_worker_status': None,
            'partner_position_type': None,
            'partner_retiree_status': None,
        }
        self.assertRaises(ValidationError, self.ser.validate, payload)

    def test_married_has_no_other_data(self):
        payload = {
            'marital_status': MaritalStatus.MARRIED,
        }
        self.assertRaises(ValidationError, self.ser.validate, payload)

    def test_married_if_worker_status_set_position_type_must_be_too(self):
        payload = {
            'marital_status': MaritalStatus.MARRIED,
            'marriage_date': 'set',
            'partner_first_name': 'set',
            'partner_last_name': 'set',
            'partner_middle_name': 'set',
            'partner_is_student': None,
            'partner_worker_status': 'set',
            'partner_position_type': None,
            'partner_retiree_status': None,
        }
        self.assertRaises(ValidationError, self.ser.validate, payload)

    def test_two_social_statuses_are_set(self):
        payload = {
            'marital_status': MaritalStatus.MARRIED,
            'marriage_date': 'set',
            'partner_first_name': 'set',
            'partner_last_name': 'set',
            'partner_middle_name': 'set',
            'partner_is_student': 'set',
            'partner_worker_status': None,
            'partner_position_type': None,
            'partner_retiree_status': 'set',
        }
        self.assertRaises(ValidationError, self.ser.validate, payload)

    def test_work_statuses_are_set_both(self):
        payload = {
            'marital_status': MaritalStatus.MARRIED,
            'marriage_date': 'set',
            'partner_first_name': 'set',
            'partner_last_name': 'set',
            'partner_middle_name': 'set',
            'partner_is_student': None,
            'partner_worker_status': 'set',
            'partner_position_type': 'set',
            'partner_retiree_status': None,
        }
        self.assertEqual(self.ser.validate(payload), payload)


class ValidateForbiddenWordsTestCase(SimpleTestCase):
    # TODO добавить тест для валидации ввода, у которого заглавные буквы расположены в неправильном порядке
    def test_check_forbidden_words_and_sequences(self):
        forb_vals = ['НЕТ', 'Нет', 'нЕт', 'TEST', '+', '[]', 'НЕТТЕСТ', '-', '–', ' ']

        for val in forb_vals:
            with self.assertRaises(ValidationError, msg=f'value {val}'):
                check_forbidden_words(val)

    def test_false_negative(self):
        allow_vals = ['Нетриков', 'тестович']

        for val in allow_vals:
            try:
               check_forbidden_words(val)
            except ValidationError:
                self.fail()


class CareerEducationValidatorTestCase(SimpleTestCase):
    ser = CareerEducationSerializer()

    def test_marital_status_corresponds_fields(self):
        payload = {
            'workplace_category': WorkplaceCategory.FULL_TIME,
            'org_name': 'set',
            'org_industry': 'set',
            'position': 'set',
            'org_ownership': 'set',
            'org_location': 'set',
            'job_phone': 'set',
            'worker_status': 'set',
            'position_type': 'set',
        }

        self.assertEqual(self.ser.validate(payload), payload)

    def test_marital_status_does_not_correspond_fields(self):
        payload = {
            'workplace_category': WorkplaceCategory.UNEMPLOYED,
            'org_name': 'set',
            'org_industry': 'set',
            'position': 'set',
            'org_ownership': 'set',
            'org_location': 'set',
            'job_phone': 'set',
            'worker_status': 'set',
            'position_type': 'set',
        }

        self.assertRaises(ValidationError, self.ser.validate, payload)

        payload = {
            'workplace_category': WorkplaceCategory.FULL_TIME,
        }

        self.assertRaises(ValidationError, self.ser.validate, payload)

    def test_if_worker_status_set_position_type_must_be_too(self):
        payload = {
            'workplace_category': WorkplaceCategory.FULL_TIME,
            'is_student': None,
            'worker_status': 'set',
            'position_type': None,
            'retiree_status': None,
        }
        self.assertRaises(ValidationError, self.ser.validate, payload)

    def test_two_social_statuses_are_set(self):
        payload = {
            'workplace_category': WorkplaceCategory.UNEMPLOYED,
            'is_student': 'set',
            'worker_status': None,
            'position_type': None,
            'retiree_status': 'set',
        }
        self.assertRaises(ValidationError, self.ser.validate, payload)

    def test_work_statuses_are_set_both(self):
        payload = {
            'is_student': None,
            'worker_status': 'set',
            'position_type': 'set',
            'retiree_status': None,
            'workplace_category': WorkplaceCategory.FULL_TIME,
            'org_name': 'set',
            'org_industry': 'set',
            'position': 'set',
            'org_ownership': 'set',
            'org_location': 'set',
            'job_phone': 'set',
        }
        self.assertEqual(self.ser.validate(payload), payload)

    def test_retiree_is_set(self):
        payload = {
            'workplace_category': WorkplaceCategory.UNEMPLOYED,
            'is_student': None,
            'worker_status': None,
            'position_type': None,
            'retiree_status': 'set',
        }
        self.assertEqual(self.ser.validate(payload), payload)

    def test_is_student_is_set(self):
        payload = {
            'workplace_category': WorkplaceCategory.UNEMPLOYED,
            'is_student': 'set',
            'worker_status': None,
            'position_type': None,
            'retiree_status': None,
        }
        self.assertEqual(self.ser.validate(payload), payload)


class PersonalDataValidatorTestCase(SimpleTestCase):
    ser = PersonalDataSerializer()

    def test_check_date_valid(self):
        yesterday = date.today() - timedelta(days=1)
        self.ser.validate_registry_date(yesterday)

    def test_check_date_invalid(self):
        yesterday = date.today()
        self.ser.validate_registry_date(yesterday)
