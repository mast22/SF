from django.utils.translation import gettext_lazy as __

from apps.common.choices import Choices


class OrderStatus(Choices):
    """ Документация о статусах системы

    Система предоставляет статусы для заказа (OrderStatus) и частно для отправки в банк (OCP) (CreditProductStatus)
    До отправки заказа на скоринг система работает только по OrderStatus
    После отправки на скоринг синхронизация статусов OCP и Order осуществляется посредством Order.update_with_status()
    После выбора кредитного продукта (choose_credit_product) мы возвращаемся к
    использованию статуса заказа и игнорируем статусы OCP
    """
    NEW = 'new', __('Новый')
    TELEGRAM = 'telegram', __('Из телеграмма')
    SCORING = 'scoring', __('Скоринг') # На этом шаге можем выбирать продукт, не дожидаясь ответа от других банков
    REJECTED = 'rejected', __('Отказ всех банков')  # Выставляется автоматически через update_with_status
    SELECTION = 'selection', __('Выбор кредитного продукта')  # Устанавливается после прихода ответа хотя бы от одного банка. Можно выбирать кред. продукт
    AGREEMENT = 'agreement', __('Заключение соглашения')  # После выбора банка для скоринга
    AGREEMENT_ERROR = 'agreement-error', __('Ошибка в заключении соглашения')  # Получили ошибку при отправке согласия клиента
    DOCUMENTS_CREATION = 'documents-creation', __('Формирование документов')
    DOCUMENTS_SIGNING = 'documents-signing', __('Ожидание подписи документов клиентом')  # Ожидание подписи,
    DOCUMENTS_SENDING = 'documents-sending', __('Отправка подписанных документов в банк')
    DOCUMENTS_ERROR = 'documents-error', __('Ошибка при обработке документов банком')  # Необходимо доработать скан-копии
    AUTHORIZATION = 'authorization', __('На авторизации')  # Авторизация договора банком
    AUTHORIZED = 'authorized', __('Авторизован')  # Подтверждение авторизации договора от банка
    UNAUTHORIZED = 'unauthorized', __('Не авторизован')  # Также включает в себя ошибку авторизации
    CLIENT_REFUSED = 'client-refused', __('Отказ клиента')  # Единственно устанавливаемый статус клиентом


ORDER_STATUSES_ACTIVE = {
    # Статусы заявки, из которых можно совершить какие-либо изменения заказа
    OrderStatus.NEW, OrderStatus.TELEGRAM, OrderStatus.SCORING,
    OrderStatus.REJECTED, OrderStatus.SELECTION, OrderStatus.AGREEMENT,
    OrderStatus.DOCUMENTS_CREATION, OrderStatus.DOCUMENTS_SIGNING,
    OrderStatus.AUTHORIZATION, OrderStatus.UNAUTHORIZED,
    OrderStatus.AGREEMENT_ERROR, OrderStatus.DOCUMENTS_ERROR,
}
ORDER_STATUSES_PASSIVE = {
    # Конечные статусы заявки, из которых нет продолжения.
    OrderStatus.REJECTED, OrderStatus.AUTHORIZED, OrderStatus.CLIENT_REFUSED,
}


# Время жизни временного токена для загрузки сканов паспортов
ORDER_TEMP_TOKEN_EXPIRES_TIMEDELTA = 60 * 60 * 24



class Education(Choices):
    ACADEMIC_DEGREE = 'acad_degree', __('Ученая степень')
    SEVERAL_DEGREES = 'sev_degrees', __('Несколько высших образований')
    HIGHER = 'high_edu', __('Высшее образование')
    HIGHER_INCOMPLETE_EDUCATION = 'high_inc_edu', __('Высшее незаконченное')
    SPECIALIZED_SECONDARY = 'spec_secondary', __('Среднее специальное')
    SECONDARY = 'secondary', __('Среднее образование')
    SECONDARY_INCOMPLETE = 'inc_higher', __('Неоконченное высшее')


class RealtyType(Choices):
    COM = 'commercial', __('Коммерческая')
    PUB = 'public', __('Публичная')
    SUB = 'private', __('Частная')


class WorkerSocialStatus(Choices):
    FULL_TIME = 'full', __('Полный рабочий день')
    PART_TIME = 'part', __('Неполный рабочий день')
    OWN_BUSINESS = 'own', __('Собственный бизнес')
    PART_OWNERSHIP = 'part_own', __('Совладелец бизнеса')
    FREE_LANCER = 'free_lan', __('Самозанятый')
    INTERN = 'intern', __('Стажировка')


class RetireeSocialStatus(Choices):
    COMMON = 'common', __('Пенсионер (без льгот)')
    BENEFICIARY = 'beni', __('Льготный пенсионер')


class Sex(Choices):
    MALE = 'male', __('Мужчина')
    FEMALE = 'female', __('Мужчина')


class Category(Choices):
    HOME_APPLIANCES = 'ha', __('Бытовая техника')
    PC_LAPTOPS = 'pc_laptops', __('ПК и Ноутбуки')
    SMARTPHONES = 'smartphones', __('Смартфоны')


class CreditProductStatus(Choices):
    """ Статусы отправки на скоринг
    Финальный статус - success
    """
    NOT_SENT = 'not-sent', __('Ещё не отправлено')
    IN_PROCESS = 'in-process', __('В процессе скоринга')
    CLIENT_REFUSED = 'client-refused', __('Клиент отказался')

    # Статусы, назначаемые после скоринга
    REJECTED = 'rejected', __('Отказ банка')
    SUCCESS = 'success', __('Одобрено банком')
    SHORT_APPROVED = 'short_approved', __('Короткая заявка одобрена, требуется отправка полной')
    GOODS_INFO_REQUIRED = 'goods_info_req', __('Требуется информация по товарам')
    SUCCESS_VALIDATION_REQUIRED = 'manual_validation_required', __('Требуется ручная проверка')
    TECHNICAL_ERROR = 'tech_error', __('Техническая ошибка, возможна повторная отправка')


PERSONAL_DATA_TEMP_TOKEN_LENGTH = 128


class PhotoType(Choices):
    MAIN = 'main', __('Главная страница')
    EXTRA = 'extra', __('Дополнительные страницы')
    CLIENT = 'client', __('Клиент')


class GoodService(Choices):
    service_1 = 'service_1', __('Первая услуга')
    service_2 = 'service_2', __('Вторая услуга')


class MaritalStatus(Choices):
    SINGLE = 'single', __('Не состоял(а) в браке')
    MARRIED = 'married', __('Состоит в браке')
    CIVIL = 'civil', __('Гражданский брак')
    DIVORCED = 'divorced', __('Разведен(а)')
    WIDOWED = 'widowed', __('Вдовец/вдова')


class LifeInsuranceCode(Choices):
    RESO = 1, '2-8S7UY86 ОСАО "РЕСО-Гарантия"'
    ALFA_1 = 2, '2-1HURJZF ООО "Альфа-Страхование-Жизнь"'
    ALFA_2 = 3, '2-OMYWQB ООО "Альфа-Страхование-Жизнь"'
    ALFA_3 = 4, '2-A62U0TR ООО "АЛЬФАСТРАХОВАНИЕ-ЖИЗНЬ"'


class WorkLossInsuranceCode(Choices):
    ALFA_1 = 1, '2-927ER1Q ОАО "АльфаСтрахование"'
    ALFA_2 = 2, '2-927EQYN ОАО "АльфаСтрахование"'
    MIL = 3, '2-5E9TTXC ОАО "Военно-страховая компания"'
    ALFA_3 = 4, '2-A62U1CG ОАО "АльфаСтрахование"'


class ContactRelation(Choices):
    BROTHER = 'BROTHER', 'Брат'
    DAUGHTER = 'DAUGHTER', 'Дочь'
    FATHER = 'FATHER', 'Отец'
    FRIEND = 'FRIEND', 'Друг / подруга'
    MOTHER = 'MOTHER', 'Мать'
    SISTER = 'SISTER', 'Сестра'
    SON = 'SON', 'Сын'
    OTHER = 'OTHER', 'Другое'
    RELATIVE = 'RELATIVE', 'Иной родственник'


class PositionType(Choices):
    """ Общие типы должностей """
    SPECIALIST = 'spec', 'Неруководящий работник'
    OWNER = 'owner', 'Предприниматель/владелец бизнеса'
    MANAGER = 'manager', 'Руководитель подразделения'
    TOP_MANAGER = 'top_man', 'Руководство организации'


class NotificationWay(Choices):
    HABITATION = 'HABITATION', __('Адрес проживания')
    REGISTRATION = 'REGISTRATION', __('Адрес прописки')


class WorkplaceCategory(Choices):
    OWN_BUSINESS = 'OWN_BUSINESS', __('Владеет собственным бизнесом')
    UNEMPLOYED = 'UNEMPLOYED', __('Безработный')
    PART_TIME = 'PART_TIME', __('Неполный рабочий день, совместительство, работа по найму')
    FULL_TIME = 'FULL_TIME', __('Полный рабочий день')


# class OwnershipType(Choices):
#     OWNSP_1 = 'Государственная компания/учреж', __('Государственная комп./учреж.')
#     OWNSP_2 = 'Частная компания', __('Частная компания')
#     OWNSP_3 = 'Индивидуальный предприниматель', __('Индивидуальный предприниматель')
#     OWNSP_4 = 'Некоммерческая организация', __('Некоммерческая организация')
#     OWNSP_5 = 'Частная компания с иностранным', __('Частная ком. с инос. капиталом')


class CarCoOwners(Choices):
    PERSONAL = 'personal', __('Личная')
    SHARED = 'Долевая собственность', __('Долевая собственность')
    CLOSE_RELATIVES = 'Близкие родственники', __('Близкие родственники')
    DISTANT_RELATIVES = 'Прочие родственники', __('Прочие родственники')
    ACQUAINTANCE = 'Знакомые', __('Знакомые')
    DO_NOT_OWN = 'not', __('Не владею')


class RejectReason(Choices):
    NO_EXPLANATION = 'NO_EXPLANATION', __('Без объяснений')
    INTEREST_RATE_TOO_HIGH = 'INTEREST_RATE_TOO_HIGH', __('Высокая процентная ставка')
    INSUFFICIENT_LIMIT = 'INSUFFICIENT_LIMIT', __('Недостаточный лимит по кредиту')
    LENGTHY_SCORING = 'LENGTHY_SCORING', __('Долгий процесс получения кредита')
    OTHER = 'OTHER', __('Прочее')
    POOR_SERVICE = 'POOR_SERVICE', __('Не устраивает качество обслуживания')
    OTHER_BANK = 'OTHER_BANK', __('Ушел в другой банк')
    AUTH_DID_NOT_COMPLETE = 'AUTH_DID_NOT_COMPLETE', __('Время для авторизации истекло')
    PAYMENT_TOO_HIGH = 'PAYMENT_TOO_HIGH', __('Высокий ежемесячный платеж')
    EARLY_REPAYMENT_COMMISSION_TOO_HIGH = 'EARLY_REPAYMENT_COMMISSION_TOO_HIGH', __(
        'Высок. комис. при досроч. погашении')
    LOAN_COMMISSION_TOO_HIGH = 'LOAN_COMMISSION_TOO_HIGH', __('Высокие комиссии по кредиту')
    LOAN_NO_MORE_NEEDED = 'LOAN_NO_MORE_NEEDED', __('Отпала необходимость в кредите')
    TECH_FAILURE = 'TECH_FAILURE', __('Технический сбой')
    BANK_REJECTION = 'BANK_REJECTION', __('Отказ Банка')


class ContractStatus(Choices):
    OUTLET = 'outlet', __('На точке')
    SENT = 'sent', __('Отправлены')
    OFFICE = 'office', __('В офисе')
    CDEK = 'cdek', __('В СДЭК')
    BANK = 'bank', __('В банке')


order_xlsx_fields = {
    'id': 'Номер заказа',
    'agent': 'Агент',
    'status': 'Статус',
    # Номер кредитного договора
    'purchase_amount': 'Полная стоимость',
    'loan_amount': 'Размер кредита',
    'initial_payment': 'Первоначальный взнос',
    # Стоимость страхования
    'term': 'Срок кредитования',
    'outlet_address': 'Адрес торговой точки',
    'bank': 'Банк',
    # Программа кредитования
    # Фактическое наличие СЖ
    # Фактическое наличие СР
    # Наличие СМС
    # Процентная ставка
    'created_at': 'Дата оформления заказа', # дата его создания
    # Дата авторизации договора
    'client_full_name': 'ФИО клиента',
    # '': 'Статус заявки в ПАО «МТС-Банк»',
    # '': 'Статус заявки в АО «Тинькофф Банк»',
    # '': 'Статус заявки в АО «АЛЬФА-БАНК»',
    # '': 'Статус заявки в АО «Почта Банк»',
    # '': 'Статус заявки в АО «ОТП Банк»',
    # '': 'Статус заявки в КБ «Ренессанс Кредит» (ООО)',
    # '': 'Кредитный продукт в ПАО «МТС-Банк»',
    # '': 'Кредитный продукт в АО «Тинькофф Банк»',
    # '': 'Кредитный продукт в АО «АЛЬФА-БАНК»',
    # '': 'Кредитный продукт в АО «Почта Банк»',
    # '': 'Кредитный продукт в АО «ОТП Банк»',
    # '': 'Кредитный продукт в КБ «Ренессанс Кредит» (ООО)',
    'outlet': 'Наименование юр. лица',
    # '': 'Выбор страховки СЖ в АО «Кредит Европа Банк»',
    # '': 'Выбор страховки СЖ в ПАО «МТС-Банк»',
    # '': 'Выбор страховки СЖ в АО «Тинькофф Банк»',
    # '': 'Выбор страховки СЖ в АО «АЛЬФА-БАНК»',
    # '': 'Выбор страховки СЖ в АО «Банк Русский Стандарт»',
    # '': 'Выбор страховки СЖ в ПАО КБ «Восточный»',
    # '': 'Выбор страховки СЖ в АО «Почта Банк»',
    # '': 'Выбор страховки СЖ в АО «ОТП Банк»',
    # '': 'Выбор страховки СЖ в КБ «Ренессанс Кредит» (ООО)',
    # '': 'Выбор страховки СР в АО «Кредит Европа Банк»',
    # '': 'Выбор страховки СР в ПАО «МТС-Банк»',
    # '': 'Выбор страховки СР в АО «Тинькофф Банк»',
    # '': 'Выбор страховки СР в АО «АЛЬФА-БАНК»',
    # '': 'Выбор страховки СР в АО «Банк Русский Стандарт»',
    # '': 'Выбор страховки СР в ПАО КБ «Восточный»',
    # '': 'Выбор страховки СР в АО «Почта Банк»',
    # '': 'Выбор страховки СР в АО «ОТП Банк»',
    # '': 'Выбор страховки СР в КБ «Ренессанс Кредит» (ООО)',
    # '': 'Причина отказа',
    # '': 'Комментарий отказа',
    # '': 'Причина отказа банка в АО «Кредит Европа Банк»',
    # '': 'Причина отказа банка в ПАО «МТС-Банк»',
    # '': 'Причина отказа банка в АО «Тинькофф Банк»',
    # '': 'Причина отказа банка в АО «АЛЬФА-БАНК»',
    # '': 'Причина отказа банка в АО «Банк Русский Стандарт»',
    # '': 'Причина отказа банка в ПАО КБ «Восточный»',
    # '': 'Причина отказа банка в АО «Почта Банк»',
    # '': 'Причина отказа банка в АО «ОТП Банк»',
    # '': 'Причина отказа банка в КБ «Ренессанс Кредит» (ООО)',


    # 'client_order': '123',
    # 'goods': 'Товары',
    # 'credit': 'credit',
    # 'family_data': 'family_data',
    # 'personal_data': 'personal_data',
    # 'passport': 'passport',
    # 'career_education': 'career_education',
    # 'extra_data': 'extra_data',
    # 'changed_at': 'changed_at',
    # 'telegram_order': 'telegram_order',
    # 'chosen_product': 'chosen_product',
    # 'credit_products': 'credit_products',
    # 'order_credit_products': 'order_credit_products',
    # 'extra_services': 'extra_services',
    # 'credit_product_commission_sum': 'credit_product_commission_sum',
    # 'extra_services_commission_sum': 'extra_services_commission_sum',
    # 'extra_services_sum': 'extra_services_sum',
    # 'history': 'history',
}


class OrderTempTokenType(Choices):
    """Типы временных токенов для заявок."""
    PASSPORT = 'passport', '/upload-passport-data/{key}/'
    DOCUMENT = 'document', '/check-document-status/{key}/'
