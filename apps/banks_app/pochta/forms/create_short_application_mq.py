from typing import List, Dict
from django.conf import settings

from apps.misc.const import AccordanceSpecifier, AccordanceCollection
from apps.orders.models import Order
from apps.partners.const import LocalityType
from ...base.forms import BaseBankForm
from apps.orders.const import MaritalStatus, Sex, Education
from datetime import datetime, timedelta

from ...base.rules import AccordanceRule, LoopRule, ConstRule, RawRule, DictRule, MethodRule, ListRule, TransformRule, \
    EnumRule, CalculatedRule

POCHTA_MARTIAL_STATUS_MAPPING = {
    MaritalStatus.SINGLE: 'Single',
    MaritalStatus.MARRIED: 'Married',
    MaritalStatus.CIVIL: 'Partner',
    MaritalStatus.DIVORCED: 'Divorced',
    MaritalStatus.WIDOWED: 'Widowed',
}

POCHTA_EDUCATION_MAPPING = {
    Education.ACADEMIC_DEGREE: 'Higher',
    Education.SEVERAL_DEGREES: 'Higher',
    Education.HIGHER: 'Higher',
    Education.HIGHER_INCOMPLETE_EDUCATION: 'Secondary',  # Незаконченное высшее - значит высшая школа
    Education.SPECIALIZED_SECONDARY: 'Secondary Spec',
    Education.SECONDARY: 'Secondary',
    Education.SECONDARY_INCOMPLETE: 'Primary',
}


def get_exp_start_date(base: Order):
    months_of_exp = base.career_education.months_of_exp
    if months_of_exp is None:
        months_of_exp = 0
    return (datetime.now() - timedelta(days=30 * months_of_exp)).strftime('%Y-%m-%d')


class CreateShortApplicationMQBankForm(BaseBankForm):
    def convert_process_list_of_addresses(self, order, mapping) -> List[Dict]:
        # Нас интересуют 2 адреса - проживания и прописки
        pass

    @staticmethod
    def convert_number_to_word_children_dependents_count(value):
        if value > 3:
            return 'More three'
        if value == 0:
            return 'Non'
        if value == 2:
            return 'Two'
        if value == 3:
            return 'Three'
        if value == 1:
            return 'One'

    list_of_contacts = ListRule('Contact', [
        {
            'MonthPersonalIncome': TransformRule('career_education.monthly_income', str),
            'MonthFamilyIncome': TransformRule('family_data.monthly_family_income', str),
            # 'MonthFamilyExpenses': {'converter': ''},
            'MaritalStatus': EnumRule('family_data.marital_status', POCHTA_MARTIAL_STATUS_MAPPING),
            'NumberChild': MethodRule('convert_number_to_word_children_dependents_count', 'family_data.children_count'),
            'NumberDepend': MethodRule('convert_number_to_word_children_dependents_count',
                                       'family_data.dependents_count', ),
            'Education': EnumRule('career_education.education', POCHTA_EDUCATION_MAPPING),
            'Gender': EnumRule('passport.sex', {Sex.MALE: 'Male', Sex.FEMALE: 'Female', }),
            'BirthPlace': CalculatedRule(
                lambda base: base.personal_data.birth_place + base.personal_data.birth_country),
            'LastName': RawRule('passport.last_name'),
            'FirstName': RawRule('passport.first_name'),
            'MiddleName': RawRule('passport.middle_name').with_presence(
                lambda payload: payload['Client_Middle_Name'] is not None),
            'NoMiddleNameFlag': CalculatedRule(lambda base: 'Y' if base.passport.middle_name is None else 'N'),
            'BirthDate': TransformRule('passport.birth_date', lambda date: date.strftime('%m/%d/%Y')),
            'PrevLastName': RawRule('extra_data.previous_last_name').with_proceed(
                lambda base: base.extra_data.previous_last_name is not None),
            'PrevFirstName': RawRule('extra_data.previous_first_name').with_presence(
                lambda payload: payload['PrevFirstName'] is not None),
            'PrevMiddleName': RawRule('extra_data.previous_middle_name').with_presence(
                lambda payload: payload['PrevMiddleName'] is not None),
            # 'SocialStatus': {'converter': ''}, # Значения очень странные, лучше оставить на потом
            'VisualAssesCode': ConstRule(0),
            'SecurityWord': RawRule('family_data.code_word'),
            'ListOfEmployers': ListRule('Employer', [
                {
                    'Employer': RawRule('career_education.org_name'),
                    # 'FioManager': {'converter': '',},
                    # 'Industry': {'converter': '',},
                    # 'EmployeeNumber': {'converter': '',},
                    'Position': AccordanceRule('career_education.position_type'),
                    'StartDate': CalculatedRule(get_exp_start_date).with_proceed(
                        lambda order: order.career_education.months_of_exp is not None
                    ),
                }
            ]),
            # 'ListOFAssets': {},
            'ListOfDocuments': ListRule('Document', [
                {
                    'Seria': RawRule('passport.series'),
                    'Number': RawRule('passport.number'),
                    'IssueBy': RawRule('passport.issued_by'),
                    'IssueByCode': RawRule('passport.division_code'),
                    'IssueDate': MethodRule('cast_date', 'passport.receipt_date'),
                }
            ]),
            'ListOfPhones': ListRule('Phone', [{
                'PhoneNumber': TransformRule('client_order.phone', lambda phone: phone.as_e164)
            }]),
            'ListOfAddress': ListRule('Address', [
                {
                    'Country': ConstRule('Russian Federation'),
                    'Zipcode': RawRule('personal_data.habitation_location.postcode'),
                    'RegionCode': TransformRule(
                        'personal_data.habitation_location.subject',
                        lambda subject_num: str(subject_num).zfill(2)
                    ),
                    'City': RawRule('personal_data.habitation_location.locality'),
                    'CityType': RawRule('personal_data.habitation_location.type'),  # TODO Accordance
                    'Street': RawRule('personal_data.habitation_location.street'),
                    'Housing': RawRule('personal_data.habitation_location.block'),
                    'Flat': RawRule('personal_data.habitation_location.place'),
                    'Building': RawRule('personal_data.habitation_location.building'),

                    'LivingAddressFlag': ConstRule('Y'),
                    'RegAddressFlag': ConstRule('N'),
                    'PostAddressFlag': ConstRule('N'),
                    'WorkAddressFlag': ConstRule('N'),
                    'DeliveryAddressFlag': ConstRule('N'),
                    'KladrFlag': ConstRule('N'),
                },
                {
                    'Country': ConstRule('Russian Federation'),
                    'Zipcode': RawRule('personal_data.registry_location.postcode'),
                    'RegionCode': TransformRule(
                        'personal_data.registry_location.subject',
                        lambda subject_num: str(subject_num).zfill(2)
                    ),
                    'City': RawRule('personal_data.registry_location.locality'),
                    'CityType': RawRule('personal_data.registry_location.type'),  # TODO Accordance
                    'Street': RawRule('personal_data.registry_location.street'),
                    'Housing': RawRule('personal_data.registry_location.block'),
                    'Flat': RawRule('personal_data.registry_location.place'),
                    'Building': RawRule('personal_data.registry_location.building'),

                    'LivingAddressFlag': ConstRule('N'),
                    'RegAddressFlag': ConstRule('Y'),
                    'PostAddressFlag': ConstRule('N'),
                    'WorkAddressFlag': ConstRule('N'),
                    'DeliveryAddressFlag': ConstRule('N'),
                    'KladrFlag': ConstRule('N'),
                }
            ])
        }
    ])

    mapper = {
        'BrokerCode': {'converter': 'convert_calculated', 'callable': lambda _: settings.POCHTA_SW_CODE},
        'ReleaseVsn': {'converter': 'convert_calculated', 'callable': lambda _: settings.POCHTA_API_VERSION},
        'Application': DictRule({
            'Type': ConstRule('POS'),
            'Channel': ConstRule('Broker'),
            'PathCode': ConstRule('PreControl'),  # TODO узнать что такое
            'TtCode': MethodRule('get_outlet_code'),
            'ToCode': MethodRule('get_outlet_code'),
            'BrokerId': ConstRule('PLACEHOLDER'),  # TODO узнать у почты
            'BrokerAgentId': MethodRule('get_agent_code'),
            'FirstPayment': RawRule('credit.initial_payment'),
            'InsuranceForm': ConstRule('PLACEHOLDER'),  # TODO узнать как правильно работает
            'FullApplication': ConstRule('1'),  # Мы целимся на полную заявку, а частичную попробуем позже
            'OptySource': ConstRule('Broker'),
            'ListOfGoods': LoopRule(
                lookup='goods',
                children_name='Goods',
                inner={
                    'Group': AccordanceRule('good.category', lambda x: x[1]),
                    'GoodCode': AccordanceRule('good.category', lambda x: x[0]),
                    'Mark': RawRule('good.brand'),
                    'Model': RawRule('good.model'),
                    'Quantity': RawRule('amount'),
                    'Price': TransformRule('price', str),
                }
            ),
            'ListOfContacts': list_of_contacts,
            'AutoScoringFlag': ConstRule('Y'),
        })
    }
