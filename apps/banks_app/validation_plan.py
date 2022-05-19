# TODO: удалить, когда пойму, зачем оно тут.
from .base.forms import BaseBankForm


class CheckFormBankForm(BaseBankForm):
    """ Форма для проверки данных заказа """

    mapper = {
        'initial_payment': {
            # Первичный платеж не должен быть больше общей суммы заказа
            # Зависит от order.purchase_amount
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        # 'term': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        'first_name': {
            # Не должно входить в запрещенные значения
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'last_name': {
            # Не должно входить в запрещенные значения
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'middle_name': {
            # Не должно входить в запрещенные значения
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'birth_date': {
            # Возраст должен быть больше 18 лет
            # Должен быть меньше 100
            'converter': 'convert_check',
            'callable': lambda order: order,
        },
        # TODO можно добавить валидацию посредством нахождения в списке невалидных паспортов
        # Можно попробовать сделать так: https://habr.com/ru/post/538358/
        'number': {
            # Валидация 4 чисел
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'series': {
            # Валидация 6 чисел
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'receipt_date': {
            # Валидация уже есть на сериалайзере можно повторить тут
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        # 'division_code': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        # 'issued_by': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        # 'sex': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        # 'passport_main_photo': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        # 'passport_registry_photo': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        # 'previous_passport_photo': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        # 'client_photo': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        # 'registry_location': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        'registry_date': {
            # Не больше текущего дня, не больше возраста клиента
            # Зависит от возраста клиента
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        # 'habitation_location': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        # 'habitation_realty_type': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        'realty_period_months': {
            # Не больше возраста клиента
            # Зависит от возраста клиента
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        # 'email': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        # 'is_student': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        # 'worker_status': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        # 'position_type': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        # 'retiree_status': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        # 'birth_place': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        # 'birth_country': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        # 'life_insurance_code': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        # 'work_loss_insurance_code': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        'contact_first_name': {
            # Не должно входить в запрещенные значения
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'contact_last_name': {
            # Не должно входить в запрещенные значения
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'contact_middle_name': {
            # Не должно входить в запрещенные значения
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        # 'contact_phone': {
        #     # Валидация того, что пользователь
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        # 'contact_relation': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        # 'appearance': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        'marital_status': {
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'marriage_date': {
            # Должен быть если клиент женат
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        # 'children_count': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        # 'dependents_count': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        'partner_first_name': {
            # Должен отсутствовать если клиент не женат
            # Не должно входить в запрещенные значения
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'partner_last_name': {
            # Должен отсутствовать если клиент не женат
            # Не должно входить в запрещенные значения
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'partner_middle_name': {
            # Должен отсутствовать если клиент не женат
            # Не должно входить в запрещенные значения
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'partner_is_student': {
            # Должен отсутствовать если клиент не женат
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'partner_worker_status': {
            # Должен отсутствовать если клиент не женат
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'partner_position_type': {
            # Должен отсутствовать если клиент не женат
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'partner_retiree_status': {
            # Должен отсутствовать если клиент не женат
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'monthly_family_income': {
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'code_word': {
            # Не должно входить в запрещенные значения
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        # 'education': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        'workplace_category': {
            # Указывать только при наличии worker_status
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        # 'monthly_income': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        # 'monthly_expenses': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        'org_name': {
            # Указывать при наличии worker_status
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'org_industry': {
            # Указывать при наличии worker_status
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'position': {
            # Указывать при наличии worker_status
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'org_ownership': {
            # Указывать при наличии worker_status
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'months_of_exp': {
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'org_location': {
            # Указывать при наличии worker_status
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'job_phone': {
            # Указывать при наличии worker_status
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        # 'notification_way': {
        #     'converter': 'convert_check',
        #     'callable': lambda order: order
        # },
        'previous_passport_series': {
            # Валидация 4 чисел
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'previous_passport_number': {
            # Валидация 6 чисел
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'previous_first_name': {
            # Не должно входить в запрещенные значения
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'previous_last_name': {
            # Не должно входить в запрещенные значения
            'converter': 'convert_check',
            'callable': lambda order: order
        },
        'previous_middle_name': {
            # Не должно входить в запрещенные значения
            'converter': 'convert_check',
            'callable': lambda order: order
        },
    }
