""" Общие структуры для анкет """
import datetime

from apps.misc.const import AccordanceSpecifier
from apps.orders.const import WorkerSocialStatus, WorkplaceCategory, Sex
from apps.orders.models import Order
from apps.partners.const import LocalityType


def get_employment_type(order: Order):
    """ Намешанная логика МТС`а """
    workplace_category = order.career_education.workplace_category
    worker_status = order.career_education.worker_status

    if worker_status == WorkerSocialStatus.PART_OWNERSHIP:
        return 'WORKACTIVITY.3'

    if worker_status == WorkerSocialStatus.OWN_BUSINESS:
        return 'WORKACTIVITY.4'

    if workplace_category == WorkplaceCategory.UNEMPLOYED:
        return 'WORKACTIVITY.7'

    if worker_status == WorkerSocialStatus.FREE_LANCER:
        return 'WORKACTIVITY.2'

    if order.career_education.is_student:
        return 'WORKACTIVITY.5'

    if order.career_education.retiree_status:
        return 'WORKACTIVITY.6'

    return 'WORKACTIVITY.1'


client_list_document = {
    # Отправляем только паспорт, скорее всего МТС больше ничего и не нужно
    'converter': 'convert_list',
    'children_name': 'clientDocument',
    'fields': [
        {
            'documentType': {'converter': 'convert_const', 'value': 'Passport'},
            'isPrimary': {'converter': 'convert_const', 'value': 'true'},
            'isActive': {'converter': 'convert_const', 'value': 'true'},
            'serial': {'converter': 'convert_raw', 'lookup': 'passport.series'},
            'number': {'converter': 'convert_raw', 'lookup': 'passport.number'},
            'issueOrgCode': {'converter': 'convert_raw', 'lookup': 'passport.division_code'},
            'issueOrgName': {'converter': 'convert_raw', 'lookup': 'passport.issued_by'},
            'issueDate': {'converter': 'convert_raw', 'lookup': 'passport.receipt_date'},
        }
    ]
}

client_list_address = {
    'converter': 'convert_dict',
    'data': {
        'clientAddress': {
            'converter': 'convert_dict',
            'data': {
                'addressType': {
                    'converter': 'convert_const',
                    'value': 'ADDRESS.TYPE.1',  # Регистрация
                },
                'countryCode': {
                    # Работаем только с Россией
                    'converter': 'convert_const',
                    'value': '643',
                },
                'countryName': {
                    # Работаем только с Россией
                    'converter': 'convert_const',
                    'value': 'Россия',
                },
                'regionName': {
                    'converter': 'convert_calculated',
                    'callable': lambda
                        order: order.personal_data.registry_location.get_subject_display(),
                },
                'regionCode': {
                    'converter': 'convert_transform',
                    'lookup': 'personal_data.registry_location.subject',
                    'callable': lambda subject_num: str(subject_num).zfill(2)
                },
                # 'regionSocr': {}, # необходимо подумать как реализовать сокращенные регионы
                'cityName': {
                    # Работаем с городом если его тип на самом деле - город
                    'converter': 'convert_raw',
                    'lookup': 'personal_data.habitation_location',
                    'proceed': lambda location: location.type == LocalityType.LOC_TYPE_5
                },
                'citySocr': {
                    # МТС хочет тип города, пишет сокращенный город, видимо им нужно название - пару букв в начале
                    'converter': 'convert_raw',
                    'lookup': 'personal_data.habitation_location.type',
                    'proceed': lambda location: location.type == LocalityType.LOC_TYPE_5
                },
                'localityName': {
                    # Работаем с другими нас пунктами если это не город
                    'converter': 'convert_raw',
                    'lookup': 'personal_data.habitation_location',
                    'proceed': lambda location: location.type != LocalityType.LOC_TYPE_5
                },
                'localitySocr': {
                    # МТС хочет тип города, пишет сокращенный город, видимо им нужно название - пару букв в начале
                    'converter': 'convert_raw',
                    'lookup': 'personal_data.habitation_location.type',
                    'proceed': lambda location: location.type != LocalityType.LOC_TYPE_5
                },
                'regBase': {
                    # TODO заглушка
                    'converter': 'convert_const',
                    'value': 'Property',
                },
                'regDate': {
                    'converter': 'convert_transform',
                    'lookup': 'personal_data.registry_date',
                    'callable': lambda date: date.strftime('%m-%d-%Y'),
                }
            }
        }
    }
}

total_outlay = {
    'converter': 'convert_dict',
    'data': {
        'summa': {
            'converter': 'convert_transform',
            'lookup': 'career_education.monthly_expenses',
            'callable': str
        },
        'currency': {
            'converter': 'convert_const',
            'value': 'RUB'
        },
    }
}

total_income = {
    'converter': 'convert_dict',
    'data': {
        'summa': {
            'converter': 'convert_transform',
            'lookup': 'career_education.monthly_income',
            'callable': str
        },
        'currency': {
            'converter': 'convert_const',
            'value': 'RUB'
        },
    }
}

client_list_work = {
    'converter': 'convert_dict',
    'data': {
        'workType': {
            # Не понимаю зачем этот аттрибут
            'converter': 'convert_const',
            'value': 'true'
        },
        'employmentType': {
            'converter': 'convert_calculated',
            'callable': get_employment_type
        },
        'workForm': {  # неможем определить ЗАО, ООО или ИП использовать
            'converter': 'convert_accordance',
            'lookup': 'career_education.org_ownership',
        },
        'fullName': {
            'converter': 'convert_raw',
            'lookup': 'career_education.org_name'
        },
        # 'sizeCompany': {
            # требует нового поля
        # },
        # 'activityType': {},  # Ждём ответа СФ. Либо спрашиваю их контакт
        # 'clientActivity': {},
        'addresses': {
            'converter': 'convert_list',
            'children_name': 'address',
            'fields': [
                # {
                #     'addressType': {},
                #     'countryName': {},
                #     'countryCode': {},
                #     'cityName': {},
                #     'citySocr': {},
                #     'localityName': {},
                #     'localitySocr': {},
                # }
            ]
        },
        # 'addForEmployment': {
            # 'converter': 'convert_list',
            # 'data': {
            #     'worker': {
            #         'positionLevel': {},
            #         'position': {},
            #         'ownWorker': {},
            #         'startDate': {},
            #         'kind': {},
            #     }
            # }
        # }
    }
}

citizenship = {
    'converter': 'convert_dict',
    'data': {
        'countryName': {
            'converter': 'convert_const',
            'value': 'Россия'
        },
        'countryCode': {
            'converter': 'convert_const',
            'value': '643'
        },
        'citizenUSA': {
            'converter': 'convert_transform',
            'lookup': 'personal_data.usa_citizenship',
            'callable': lambda v: 'true' if v else 'false'
        }
    }
}

client_common_data = {
    'converter': 'convert_dict',
    'data': {
        'family': {
            'converter': 'convert_raw',
            'lookup': 'passport.last_name',
        },
        'name': {
            'converter': 'convert_raw',
            'lookup': 'passport.first_name',
        },
        'fatherName': {
            'converter': 'convert_raw',
            'lookup': 'passport.middle_name',
            'proceed': lambda order: order.passport.middle_name is not None
        },
        'birthDate': {
            'converter': 'convert_transform',
            'lookup': 'passport.birth_date',
            'callable': lambda date: date.strftime('%m-%d-%Y'),
        },
        'clientSex': {
            'converter': 'convert_enum',
            'lookup': 'passport.sex',
            'mapper': {Sex.MALE: 'M', Sex.FEMALE: 'F', }
        },
        'birthPlace': {'converter': 'convert_raw', 'lookup': 'personal_data.birth_place'},
        # 'birthPlaceKladr': {}, # Необходим ввод места рождения в интерфейсе
        'citizenship': citizenship,
        'residence': {
            'converter': 'convert_dict',
            'data': {
                'countryName': {
                    'converter': 'convert_const',
                    'value': 'Россия'
                },
                'countryCode': {
                    'converter': 'convert_const',
                    'value': '643'
                },
            }
        },
        # 'statusIPDL': {'converter': ''}, # Пока не работаем с лицами имеющими отношение
        # с иностранными гос-вами
        'codeWord': {'converter': 'convert_raw', 'lookup': 'family_data.code_word'},
        'total_experiance': {
            'converter': 'convert_raw',
            'lookup': 'career_education.months_of_exp',
        },
        'flag_allow_pass_BKI': {
            # Поверку в БКИ всегда отправляем true
            'converter': 'convert_const',
            'value': 'true'
        },
        'flag_allow_pass_BKI_Date': {
            'converter': 'convert_transform',
            'lookup': 'created_at',
            'callable': lambda date: date.strftime('%m-%d-%Y'),
        },
        'totalIncome': total_income,
        'totalOutlay': total_outlay,
    }
}

specific_data = {
    'converter': 'convert_dict',
    'data': {
        'requestData': {
            'converter': 'convert_dict',
            'data': {
                'registrationDate': {
                    'converter': 'convert_transform',
                    'lookup': 'created_at',
                    'callable': lambda created_at: datetime.date.strftime(created_at, '%Y-%m-%d')
                },
                'franchise_code': {'converter': 'convert_method', 'method_name': 'get_partner_code'},
                'mts_pos_code': {'converter': 'convert_method', 'method_name': 'get_outlet_code'},
                'mts_pos_reg_code': {
                    'converter': 'convert_transform',
                    'lookup': 'outlet.address.subject',
                    'callable': lambda subject_num: str(subject_num).zfill(2)
                },
                'mts_pos_address': {'converter': 'convert_method', 'method_name': 'get_outlet_address'},
                # 'kladr_reg_code': {},
                'userCode': {'converter': 'convert_method', 'method_name': 'get_agent_code'},
                'userFIO': {'converter': 'convert_raw', 'lookup': 'agent.full_name'},
                'initialPayment': {'converter': 'convert_raw', 'lookup': 'credit.initial_payment'},
                'summa_buy': {'converter': 'convert_raw', 'lookup': 'purchase_amount'},
                # У мтс стоит тип "Сумма"
                # 'purchases': {},  # TODO
                # 'discountPercent': {},
            }
        },
        # 'documents': {},
    }
}
