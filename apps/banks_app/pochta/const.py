from apps.common.choices import Choices
from apps.orders.const import CreditProductStatus



class PochtaOrderStages(Choices):
    """Стадии заявки в Почта-банке"""
    OPENED = 'SettAcc Opened', 'Договор РКО открыт'
    QES = 'Request QES', 'Запрос КЭП'
    SIGN_SETACC = 'Sign SettAcc', 'Оформление РКО'
    SIGN_CURACC = 'Sign СurrAcc', 'Оформление Сберсчета'
    AGENT_START = 'Agent Start', 'Первичная работа'
    CAR_CREDITING = 'Car Crediting', 'Принято решение по авто'
    SB_CHECK = 'Security Service Check', 'Проверка СБ'
    SFM_CHECK = 'Financial Monitoring Check', 'Проверка СФМ'
    RESERVE = 'Reserve SettAcc', 'Резервирование РКО'
    CORP_AGENT = 'Corporate Business Agent', 'Сотрудник корп. бизнеса'
    SCORING = 'Scoring', 'Скоринг'
    WAIT_DOC = 'Agent Wait Doc', 'Ожидание документов'
    DECISION = 'Agent Decision', 'Принятие решения'
    BACK_OFFICE = 'Back Office', 'Бэкофис'
    PRECONTROL = 'Precontrol', 'Предконтроль'
    PF_GENERATION = 'PF Generation', 'Формирование ПФ'
    AGREEMENT = 'Agent Agreement', 'Подписание договора'
    POSTCONTROL = 'Postcontrol', 'Постконтроль'
    ABS = 'ABS', 'АБС'
    CREDIT_INSPERCTOR = 'Credit Inspector', 'Кредитный инспектор'
    CARD_PRINT = 'Local Card Print', 'Печать локальной карты'
    CALL = 'Call', 'Обзвон'
    AUTH_WAIT = 'Authorisation Waiting', 'Ожидание авторизации'
    VERIFICATION = 'Verification', 'Верификация'
    WAITING_ACRM = 'Waiting ACRM', 'Проверка наличия предложений'
    REFINANCING = 'Agent Refinancing', 'Рефинансирование'



class PochtaOrderStatus(Choices):
    """Статусы заявки в Почта-банке"""
    COMPLETION = 'Completion', 'Дозаполнение'
    NEW = 'New', 'Новая'
    CHECK_PENDING = 'Check Pending', 'Ожидание проверки'
    PREPROCESS = 'Preprocess', 'Предварительная обработка'
    CHECKING_CAR = 'Checking Car', 'Проверка автомобиля'
    STARTED = 'Started', 'Отправлена в СПР'
    APPROVED = 'Approved', 'Одобрена'
    AUTHORIZED = 'Authorised', 'Авторизована'
    DONE = 'Done', 'Исполнена'
    CANCELLED = 'Cancelled', 'Отклонена'
    ERROR = 'Error', 'Ошибка'
    EXPIRED = 'Expired', 'Просрочена'
    ON_COMPLETION = 'On Completion', 'На доработке'
    FINAL_CHECK = 'Final Check', 'Финальная проверка'
    PREAPPROVED = 'Preapproved', 'Предодобрена'
    FILLING_CC = 'Filling in CC', 'Заполнение в КС'
    REFINANCING = 'Started Refinancing', 'Проверка рефинансирования'
    WORK = 'Work', 'В работе'
    FOR_EXAMINE = 'For Examine', 'Для рассмотрения'
    DELAYED = 'Delayed', 'Отложена'


class DecisionCode(Choices):
    """Ответ на CheckScoringResult - одобрена ли заявка"""
    PRE_APPROVED = 'PreApproved', 'предварительное одобрение (статус =Предодобрен", стадия="Принятие решения")'
    APPROVED = 'Approved', 'одобрение (статус =Одобрена, стадия=Принятие решения)'
    REJECT = 'Reject', 'отказ (статус=Отклонена, стадия=Первичная работа)'
    LATER = 'Later', 'решение еще не принято (статус = Отправлена в СПР, стадия = Первичная работа'


POCHTA_CREDIT_DECISIONS = {
    # Маппер ответов Почта-банка
    DecisionCode.LATER: CreditProductStatus.IN_PROCESS,
    DecisionCode.APPROVED: CreditProductStatus.SUCCESS,
    DecisionCode.PRE_APPROVED: CreditProductStatus.SHORT_APPROVED,
    DecisionCode.REJECT: CreditProductStatus.REJECTED,
}


class DocumentsCheckResult(Choices):
    """Ответы Почта-банка на запрос печатных форм. (Поле DocumentsCheckResult)"""
    DATA_ERROR = 'DataError', 'ошибка в данных, заявка отклонена. Перечень указан в тексте ошибки_x000D_'
    APPROVED = 'Approved', 'проверка завершена успешно, заявка одобрена_x000D_'
    NEED_DOCS = 'NeedDocs', 'часть документов не прикреплена, или нечитаема, заявка отправлена на доработку, необходимо повторно отправить документы. Перечень указан в тексте ошибки_x000D_'
    LATER = 'Later', 'результат проверки неизвестен, необходимо повторить запрос'


class DocTypes(Choices):
    """"""
    PASSPORT_PAGE_2 = 'Page Passport 2', '2-я страница паспорта/разворот'
    VOICE_GOST = 'VoiceGOST', 'Голос по ГОСТ'
    MEMBER_PASSPORT = 'Member Passport', 'Копия паспорта представителя'
    MEMBER_RIGHTS = 'Member representative rights', 'Подтвержд. прав представителя'
    CHECK_RESUL = 'CheckResult', 'Результат проверки на сайте'
    MANDATE_SCAN = 'Scan Mandate', 'Скан с оригинала доверенности'
    MANDATE_SCREEN = 'Screenshot Proof Mandate', 'Скриншот с ресурса проверки'
    AGREE_PERS = 'AgreePers', 'Согласие на кредитный отчет'
    CONSENT_SES = 'ConsentSES', 'Соглашение ПЭП'
    MIGRATION_SERT = 'Migration Sertifikat', 'Форма самосертификации'
    PHOTO = 'Photo', 'Фотография'
    PHOTO_GOST = 'PhotoGOST', 'Фотография по ГОСТ'
    WORK_PERMIT = 'WorkPermit', 'Разрешение на работу'
    PASSPORT_PAGE_3 = 'Page Passport 3', '3-я страница паспорта'
    PATENT = 'Patent', 'Патент на работу'
    PASSPORT_ADDRESS = 'Page Passport Address', 'Страница паспорта с адресом'
    DOC_SECOND = 'Second Document', 'Второй документ'
    DOC_THIRD = 'Third Document', 'Третий документ (доход)'
    PASSPORT_PAGE_4_5 = 'разворот 4 и 5 стр. паспорта', 'разворот 4 и 5 стр. паспорта'
    PAYMENT_SCHEDULE = 'Schedule Payment', 'График платежей'
    PASSPORT_PAGE_5 = 'Application', 'Page Passport 5'
    FORM_SURVEY = 'Form', 'Анкета'
    APP_BROKER = 'ApplicationBroker', 'Заявление о предост-и кредита'
    DOCUMENTS_LIST = 'Documents List', 'Список документов'
    APP_PAGE_1 = 'Page Application 1', '1-я страница заявления'
    APP_PAGE_2 = 'Page Application 2', '2-я страница заявления'
    FORM_GO = 'Form Go', 'Анкета Пойдем'
    PASSPORT_ALIEN = 'Alien Passport', 'Иностранный паспорт'
    CONF_PAGE_1 = 'Page1Sogl', '1-я страница согласия'
    CONF_PAGE_2 = 'Page2Sogl', '2-я страница согласия'
    CONF_PAGE_3 = 'Page3Sogl', '3-я страница согласия'
    CONF_PAGE_4 = 'Page4Sogl', '4-я страница согласия'
    CONF_PAGE_5 = 'Page5Sogl', '5-я страница согласия'
    CONF_PAGE_6 = 'Page6Sogl', '6-я страница согласия'
    DOCUMENT_FD= 'DocumentFD', 'Документ из FD'
    DOVER = 'Dover', 'Доверенность'
    AGREEMENT_OTHER_BANK = 'Credit agreement in other Bank', 'Кредитный договор в др-м банке'
    CREDIT_HISTORY = 'Credit history', 'Кредитная история'
    PERM_RESIDENCY = 'Permanent Residency', 'Вид на жительство'
    VISA = 'Visa', 'Виза'
    ACTION_COUPON = 'Action coupon', 'Купон на участие в акции'
    MIGRATION_CARD = 'Migration Card', 'Миграционная карта'
    TEMP_RESIDENCY_PERMIT = 'Temporary Residency Permit', 'Разрешение на врем. пребывание'
    LAND_AGREEMENT = 'Land agreement', 'Договор на землю'
    PHOTO_TEMP = 'TempPhoto', 'Временная фотография'
    CONF_OBR_1 = 'Sogl_obr_data_1', 'Согласие на взаимодействие 3л'

