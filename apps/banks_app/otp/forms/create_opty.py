from copy import copy
from django.conf import settings
from apps.common.utils import compose_full_name, value_or_zero
from apps.orders.const import Sex, Education, MaritalStatus, NotificationWay
from apps.partners.const import LocalityType
from ...base.forms import BaseBankForm
from ...base.rules import CalculatedRule, MethodRule, ConstRule, RawRule, TransformRule, EnumRule, AccordanceRule, \
    LoopRule, ListRule

OTP_EDUCATION_MAPPING = {
    Education.ACADEMIC_DEGREE: 'Graduate Degree',
    Education.SEVERAL_DEGREES: 'Post-Graduate Work',
    Education.HIGHER: 'Undergraduate Degree',
    Education.HIGHER_INCOMPLETE_EDUCATION: 'No Formal Education',
    Education.SPECIALIZED_SECONDARY: 'Professional School',
    Education.SECONDARY: 'Some High School',
    Education.SECONDARY_INCOMPLETE: 'Some Primary School',
}

OTP_MARTIAL_STATUS_MAPPING = {
    MaritalStatus.SINGLE: 'Single',
    MaritalStatus.MARRIED: 'Married',
    MaritalStatus.CIVIL: 'Partner',
    MaritalStatus.DIVORCED: 'Separated',
    MaritalStatus.WIDOWED: 'Widowed',
}


def modify_list_of_goods_base(base):
    # Если количество товара больше 1, то делаем такое же количество копий товара
    # Отп всегда принимает товары в количестве 1, даже копии
    new_base = []
    for og in base.all():
        amount = og.amount
        if amount != 1:
            og.amount = 1
            copies = []
            for i in range(amount):
                copies.append(copy(og))
            new_base += copies
            continue
        new_base.append(og)
    return new_base


class CreateOptyBankForm(BaseBankForm):
    def get_passport_series(self, value: str) -> str:
        """ Тестовые данные, который в любом случае проходят скоринг """
        if settings.PLUG_MODE:
            return '0000'
        return value

    def get_last_name(self, value: str) -> str:
        """ Тестовые данные, который в любом случае проходят скоринг """
        if settings.PLUG_MODE:
            return 'ОКОВЫЙ'
        return value

    mapper = {
        # Идентификатор среды ПО Кредитный Брокер
        'Environment_Code': CalculatedRule(lambda _: settings.OTP_SW_CODE),
        # Код торговой точки в ПО Кредитный Брокер
        'TT_Ext_Code': MethodRule('get_outlet_code'),
        # Код агента
        'Agent_Ext_Code': MethodRule('get_agent_code'),
        # Код сети (партнера)
        'Chain_code': MethodRule('get_partner_code'),
        'Opty_Type': ConstRule('Full'),
        'Paperless_Denial_Flg': ConstRule('Y'),
        'Scoring_Cart_Goods': ConstRule('N'),
        'Client_Last_Name': MethodRule('get_last_name', 'passport.last_name'),
        'Client_First_Name': RawRule('passport.first_name'),
        'Client_Middle_Name': RawRule('passport.middle_name').with_presence(
            lambda payload: payload['Client_Middle_Name'] is not None),
        'Birth_Date': TransformRule('passport.birth_date', lambda date: date.strftime('%m/%d/%Y')),
        'Country_of_Birth': RawRule('personal_data.birth_country'),
        'ID_Doc_Type': ConstRule('Паспорт гражданина РФ'),
        'ID_Doc_Series': MethodRule('get_passport_series', 'passport.series'),
        'ID_Doc_Number': RawRule('passport.number'),
        'ID_Doc_Unit_Name': RawRule('passport.issued_by'),
        'ID_Doc_Unit_Code': RawRule('passport.division_code'),
        'ID_Doc_Issue_Date': MethodRule('cast_date', 'passport.receipt_date'),
        'Citizenship': ConstRule('RU'),
        'Education': EnumRule('career_education.education', OTP_EDUCATION_MAPPING),
        'Sex': EnumRule('passport.sex', {Sex.MALE: 'M', Sex.FEMALE: 'F', }),
        'Not_Resident': ConstRule('N'),
        'Code_Word': RawRule('family_data.code_word'),
        'Place_of_Birth': RawRule('personal_data.birth_place'),
        'Worker_flg': TransformRule('career_education.worker_status', lambda status: 'Y' if bool(status) else 'N'),
        'Student_flg': TransformRule('career_education.is_student', lambda is_student: 'Y' if is_student else 'N'),
        'Retiree_flg': TransformRule('career_education.retiree_status', lambda status: 'Y' if bool(status) else 'N'),
        'Marital_Status': EnumRule('family_data.marital_status', OTP_MARTIAL_STATUS_MAPPING),
        'Partner_FIO': CalculatedRule(lambda base: compose_full_name(
            base.family_data.partner_last_name,
            base.family_data.partner_first_name,
            base.family_data.partner_middle_name,
        )),
        'Number_of_children': TransformRule('family_data.children_count', value_or_zero),
        'Number_of_dependents': TransformRule('family_data.dependents_count', value_or_zero),
        'Personal_Income': TransformRule('career_education.monthly_income', str),
        'Family_Income': TransformRule('family_data.monthly_family_income', str),
        'Mobile_Phone': TransformRule('client_order.phone', lambda phone: phone.as_e164),
        # У документации он указан необязательный, но при отправки на скоринг на самом деле он требуется
        # Немного схитрим и укажем личный мобильный телефон
        'Fact_Living_Phone': TransformRule('client_order.phone', lambda phone: phone.as_e164),
        'Registry_Address_Zipcode': RawRule('personal_data.habitation_location.postcode'),
        'Registry_Address_Country': ConstRule('RU'),
        'Registry_Address_Region': TransformRule(
            'personal_data.registry_location.subject',
            lambda subject_num: str(subject_num).zfill(2)
        ),
        'Registry_Address_City': TransformRule(
            'personal_data.registry_location',
            lambda location: location.locality if location.type != LocalityType.LOC_TYPE_5 else ''
        ),
        'Registry_Address_Town': TransformRule(
            'personal_data.registry_location',
            lambda location: location.locality if location.type == LocalityType.LOC_TYPE_5 else ''
        ),
        'Registry_Address_Date': TransformRule(
            'personal_data.registry_date',
            lambda date: date.strftime('%m/%d/%Y')
        ),
        'Fact_Registry_Address_Flg': TransformRule(
            'personal_data.habitation_location',
            lambda hab_loc: 'Y' if hab_loc is None else 'N'
        ),
        'Fact_Address_Zipcode': RawRule('personal_data.habitation_location.postcode').with_presence(
            lambda mapper: mapper['Fact_Registry_Address_Flg'] == 'N'),
        'Fact_Address_Country': ConstRule('RU').with_presence(
            lambda mapper: mapper['Fact_Registry_Address_Flg'] == 'N'),
        'Fact_Address_Region': TransformRule(
            'personal_data.habitation_location.subject',
            lambda subject_num: str(subject_num).zfill(2)
        ).with_presence(lambda mapper: mapper['Fact_Registry_Address_Flg'] == 'N'),
        'Fact_Address_City': TransformRule(
            'personal_data.habitation_location',
            lambda location: location.locality if location.type != LocalityType.LOC_TYPE_5 else ''
        ),
        'Fact_Address_Town': TransformRule(
            'personal_data.habitation_location',
            lambda location: location.locality if location.type == LocalityType.LOC_TYPE_5 else ''
        ),
        'Fact_Address_Period': RawRule('personal_data.realty_period_months'),
        'Post_Address_Flag': EnumRule('extra_data.notification_way', {
            NotificationWay.REGISTRATION: 'R',
            NotificationWay.HABITATION: 'F',
        }),
        'Work_Category': ConstRule('Main Work').with_presence(lambda mapper: mapper['Worker_flg'] == 'Y'),
        'Organization_Name': RawRule('career_education.org_name')
            .with_presence(lambda mapper: mapper['Worker_flg'] == 'Y'),
        'Form_of_Ownership': AccordanceRule('career_education.org_ownership',)
            .with_presence(lambda payload: payload['Worker_flg'] == 'Y'),
        'Industry': AccordanceRule('career_education.org_industry')
            .with_presence(lambda mapper: mapper['Worker_flg'] == 'Y'),
        'Position': AccordanceRule('career_education.position_type')
            .with_presence(lambda mapper: mapper['Worker_flg'] == 'Y'),
        'Period_of_work': RawRule('career_education.months_of_exp')
            .with_presence(lambda payload: payload['Worker_flg'] == 'Y'),
        'Work_phone1': RawRule('career_education.job_phone')
            .with_presence(lambda payload: payload['Worker_flg'] == 'Y'),
        'Work_Address_Zipcode': RawRule('career_education.org_location.postcode')
            .with_proceed(lambda order: order.career_education.org_location is not None)
            .with_presence(
            lambda mapper: mapper['Worker_flg'] == 'Y'),
        'Work_Address_Country': ConstRule('RU').with_presence(lambda mapper: mapper['Worker_flg'] == 'Y'),
        'Work_Address_Region': TransformRule(
            lookup='career_education.org_location.subject',
            func=lambda subject_num: str(subject_num).zfill(2),
        )
            .with_proceed(lambda order: order.career_education.org_location is not None)
            .with_presence(lambda mapper: mapper['Worker_flg'] == 'Y'),
        'Work_Address_City': TransformRule(
            lookup='career_education.org_location',
            func=lambda location: location.locality if location.type != LocalityType.LOC_TYPE_5 else '',
        )
            .with_presence(lambda mapper: mapper['Worker_flg'] == 'Y')
            .with_proceed(lambda order: order.career_education.org_location is not None),
        'Work_Address_Town': TransformRule(
            lookup='career_education.org_location',
            func=lambda location: location.locality if location.type == LocalityType.LOC_TYPE_5 else '',
        )
            .with_presence(lambda mapper: mapper['Worker_flg'] == 'Y')
            .with_proceed(lambda order: order.career_education.org_location is not None),
        'Product_Code': MethodRule('get_product_code'),
        'Credit_Period': RawRule('credit.term'),
        'First_Payment': TransformRule('credit.initial_payment', str),
        'ListOfServiceProgram': {
            'converter': 'convert_loop',
            'other_base': 'ocp',
            'lookup': 'extra_services',
            'children_name': 'ServiceProgram',
            'inner': {
                'ProgramName': {
                    'converter': 'convert_raw',
                    'lookup': 'name'
                },
                # 'PackNumber': {
                #     'converter': 'convert_const',
                #     'value': 'PLACEHOLDER',
                #     'presence': lambda _: False
                # },
            },
        },
        # 'ListOfServiceProgram': LoopRule(
        #
        # ),
        'Insurance_Life_Flg': ConstRule('N'),
        # 'Insurance_Life_Company': {'converter': 'convert_const', 'value': 'PLACEHOLDER'},
        'Insurance_Work_Flg': ConstRule('N'),
        # 'Insurance_Work_Company': {'converter': 'convert_const', 'value': 'PLACEHOLDER'},
        'In_BKI_Flg': ConstRule('Y'),
        'Out_BKI_Flg': ConstRule('Y'),
        'Customer_Estimate': AccordanceRule('personal_data.appearance'),
        'ListOfGoods': LoopRule(
            lookup='goods',
            children_name='Good',
            inner={
                'Category': AccordanceRule('good.category'),
                'Name': RawRule('good.name'),
                'Marka': RawRule('good.brand'),
                'Model': RawRule('good.model'),
                'Price': TransformRule('price', str),
                'Quantity': ConstRule(1),
                # TODO раскомментировать
                # 'SerialNumber': RawRule('serial_number'),
                # 'ListOfGoodServiceProgram': LoopRule(
                #     lookup='good_services',
                #     children_name='ServiceProgram',
                #     inner={
                #         'ProgramName': AccordanceRule('type'),
                #     },
                # ),
            }
        ).with_modify_items_method(modify_list_of_goods_base),
        # Необязательные поля, но предусмотренные формой по заполнению
        'Contact_Person_FIO': CalculatedRule(func=lambda base: compose_full_name(
            base.personal_data.contact_last_name,
            base.personal_data.contact_first_name,
            base.personal_data.contact_middle_name,
        )),
        'Contact_Person_Phone': TransformRule('personal_data.contact_phone', lambda phone: phone.as_e164),
        'Client_Email': RawRule('personal_data.email').with_presence(lambda _: False),
        'ListOfOpportunityAttachment': ListRule(
            children_name='OpportunityAttachment',
            fields=[
                {
                    'DocumentType': ConstRule('Паспорт гражданина РФ'),
                    'OpptyFileName': MethodRule('cast_filename', 'passport.passport_main_photo'),
                    'OpptyFileExt': MethodRule('cast_file_extension', 'passport.passport_main_photo'),
                    'OpptyFileBuffer': MethodRule('cast_file_base64', 'passport.passport_main_photo'),
                },
                {
                    'DocumentType': ConstRule('Фотография'),
                    'OpptyFileName': MethodRule('cast_filename', 'passport.client_photo'),
                    'OpptyFileExt': MethodRule('cast_file_extension', 'passport.client_photo'),
                    'OpptyFileBuffer': MethodRule('cast_file_base64', 'passport.client_photo'),
                },
            ]
        )
    }
