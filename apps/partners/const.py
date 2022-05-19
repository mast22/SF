from apps.common.choices import Choices
from django.utils.translation import gettext_lazy as __


class OutletStatus(Choices):
    """Блокировка и удаление торговой точки"""
    ACTIVE = 'active', __('Активен')
    BLOCKED = 'blocked', __('Заблокирован')
    REMOVED = 'removed', __('Удалён')



class Country(Choices):
    RU = 'RU', __('Россия')
    JP = 'JP', __('Япония')
    ET = 'ET', __('Эфиопия')
    EE = 'EE', __('Эстония')
    ER = 'ER', __('Эритрея')
    EC = 'EC', __('Эквадор')
    LK = 'LK', __('Шри-Ланка')
    SE = 'SE', __('Швеция')
    CH = 'CH', __('Швейцария')
    CZ = 'CZ', __('Чехия')
    TD = 'TD', __('Чад')
    HR = 'HR', __('Хорватия')
    FR = 'FR', __('Франция')
    FI = 'FI', __('Финляндия')
    PH = 'PH', __('Филиппины')
    UA = 'UA', __('Украина')
    UZ = 'UZ', __('Узбекистан')
    UG = 'UG', __('Уганда')
    TR = 'TR', __('Турция')
    TM = 'TM', __('Туркменистан')
    TN = 'TN', __('Тунис')
    TZ = 'TZ', __('Танзания')
    TH = 'TH', __('Тайланд')
    TJ = 'TJ', __('Таджикистан')
    TW = 'TW', __('Тайвань')
    SL = 'SL', __('Сьерра-Леоне')
    SD = 'SD', __('Судан')
    SO = 'SO', __('Сомали')
    SI = 'SI', __('Словения')
    SK = 'SK', __('Словакия')
    SY = 'SY', __('Сирия')
    SG = 'SG', __('Сингапур')
    CS = 'CS', __('Сербия и Черногория')
    RS = 'RS', __('Сербия')
    KN = 'KN', __('Сент - Китс и Невис')
    SN = 'SN', __('Сенегал')
    SC = 'SC', __('Сейшелы')
    US = 'US', __('США')
    RO = 'RO', __('Румыния')
    RW = 'RW', __('Руанда')
    PT = 'PT', __('Португалия')
    PL = 'PL', __('Польша')
    PE = 'PE', __('Перу')
    PY = 'PY', __('Парагвай')
    PA = 'PA', __('Панама')
    PS = 'PS', __('Палестинская Территория')
    PK = 'PK', __('Пакистан')
    IM = 'IM', __('Остров Мэн')
    OM = 'OM', __('Оман')
    AE = 'AE', __('Объединенные Арабские Эмираты')
    NO = 'NO', __('Норвегия')
    NZ = 'NZ', __('Новая Зеландия')
    NG = 'NG', __('Нигерия')
    NP = 'NP', __('Непал')
    NR = 'NR', __('Науру')
    MM = 'MM', __('Мьянма')
    MN = 'MN', __('Монголия')
    MD = 'MD', __('Молдавия')
    MZ = 'MZ', __('Мозамбик')
    MX = 'MX', __('Мексика')
    MA = 'MA', __('Марокко')
    ML = 'ML', __('Мали')
    MY = 'MY', __('Малазия')
    KW = 'KW', __('Кувейт')
    MK = 'MK', __('Македония')
    CU = 'CU', __('Куба')
    MG = 'MG', __('Мадагаскар')
    CI = 'CI', __('Кот Дивуар')
    MR = 'MR', __('Мавритания')
    KR = 'KR', __('Корея (Республика)')
    MU = 'MU', __('Маврикий')
    KP = 'KP', __('Корея (КНДР)')
    LU = 'LU', __('Люксембург')
    CD = 'CD', __('Конго, Демократическая Республика')
    LI = 'LI', __('Лихтенштейн')
    CG = 'CG', __('Конго')
    LT = 'LT', __('Литва')
    KM = 'KM', __('Коморские острова')
    LB = 'LB', __('Ливан')
    CO = 'CO', __('Колумбия')
    LR = 'LR', __('Либерия')
    CN = 'CN', __('Китай')
    LV = 'LV', __('Латвия')
    KG = 'KG', __('Киргизстан')
    CY = 'CY', __('Кипр')
    KE = 'KE', __('Кения')
    CA = 'CA', __('Канада')
    CM = 'CM', __('Камерун')
    KZ = 'KZ', __('Казахстан')
    YE = 'YE', __('Йемен')
    IT = 'IT', __('Италия')
    ES = 'ES', __('Испания')
    IS = 'IS', __('Исландия')
    IE = 'IE', __('Ирландия')
    IR = 'IR', __('Иран')
    IQ = 'IQ', __('Ирак')
    JO = 'JO', __('Иордания')
    ID = 'ID', __('Индонезия')
    IN = 'IN', __('Индия')
    IL = 'IL', __('Израиль')
    ZW = 'ZW', __('Зимбабве')
    WS = 'WS', __('Западное Самоа')
    ZM = 'ZM', __('Замбия')
    EG = 'EG', __('Египет')
    DO = 'DO', __('Доминиканская Республика')
    DK = 'DK', __('Дания')
    GE = 'GE', __('Грузия')
    GR = 'GR', __('Греция')
    HK = 'HK', __('Гонконг')
    NL = 'NL', __('Голландия')
    GI = 'GI', __('Гибралтар')
    DE = 'DE', __('Германия')
    GW = 'GW', __('Гвинея-Бисау')
    GN = 'GN', __('Гвинея')
    GT = 'GT', __('Гватемала')
    GH = 'GH', __('Гана')
    GY = 'GY', __('Гайана')
    HT = 'HT', __('Гаити')
    VN = 'VN', __('Вьетнам')
    LA = 'LA', __('Вьентьян')
    VI = 'VI', __('Виргинские острова (США)')
    VG = 'VG', __('Виргинские острова (Британия)')
    VE = 'VE', __('Венесуэла')
    HU = 'HU', __('Венгрия')
    GB = 'GB', __('Великобритания')
    VU = 'VU', __('Вануату')
    BI = 'BI', __('Бурунди')
    IO = 'IO', __('Британские территории в Индийском океане')
    BR = 'BR', __('Бразилия')
    BA = 'BA', __('Босния и Герцеговина')
    BO = 'BO', __('Боливия')
    BG = 'BG', __('Болгария')
    BM = 'BM', __('Бермудские острова')
    BJ = 'BJ', __('Бенин')
    BE = 'BE', __('Бельгия')
    BY = 'BY', __('Белоруссия')
    BZ = 'BZ', __('Белиз')
    BH = 'BH', __('Бахрейн')
    BD = 'BD', __('Бангладеш')
    BS = 'BS', __('Багамы')
    AF = 'AF', __('Афганистан')
    AM = 'AM', __('Армения')
    AR = 'AR', __('Аргентина')
    AG = 'AG', __('Антигуа и Барбуда')
    AD = 'AD', __('Андорра')
    AO = 'AO', __('Ангола')
    DZ = 'DZ', __('Алжир')
    AL = 'AL', __('Албания')
    AZ = 'AZ', __('Азербайджан')
    AT = 'AT', __('Австрия')
    AU = 'AU', __('Австралия')
    ZA = 'ZA', __('Южно-Африканская Республика')
    SA = 'SA', __('Саудовская Аравия')
    SR = 'SR', __('Суринам')
    TG = 'TG', __('Того')


REGION_CHOICES = (
    (1, __('Республика Адыгея (Адыгея)')),
    (2, __('Республика Башкортостан')),
    (3, __('Республика Бурятия')),
    (4, __('Республика Алтай')),
    (5, __('Республика Дагестан')),
    (6, __('Республика Ингушетия')),
    (7, __('Кабардино-Балкарская Республика')),
    (8, __('Республика Калмыкия')),
    (9, __('Карачаево-Черкесская Республика')),
    (10, __('Республика Карелия')),
    (11, __('Республика Коми')),
    (12, __('Республика Марий Эл')),
    (13, __('Республика Мордовия')),
    (14, __('Республика Саха (Якутия)')),
    (15, __('Республика Северная Осетия - Алания')),
    (16, __('Республика Татарстан (Татарстан)')),
    (17, __('Республика Тыва')),
    (18, __('Удмуртская Республика')),
    (19, __('Республика Хакасия')),
    (20, __('Чеченская Республика')),
    (21, __('Чувашская Республика - Чувашия')),
    (22, __('Алтайский край')),
    (23, __('Краснодарский край')),
    (24, __('Красноярский край')),
    (25, __('Приморский край')),
    (26, __('Ставропольский край')),
    (27, __('Хабаровский край')),
    (28, __('Амурская область')),
    (29, __('Архангельская область')),
    (30, __('Астраханская область')),
    (31, __('Белгородская область')),
    (32, __('Брянская область')),
    (33, __('Владимирская область')),
    (34, __('Волгоградская область')),
    (35, __('Вологодская область')),
    (36, __('Воронежская область')),
    (37, __('Ивановская область')),
    (38, __('Иркутская область')),
    (39, __('Калининградская область')),
    (40, __('Калужская область')),
    (41, __('Камчатский край')),
    (42, __('Кемеровская область')),
    (43, __('Кировская область')),
    (44, __('Костромская область')),
    (45, __('Курганская область')),
    (46, __('Курская область')),
    (47, __('Ленинградская область')),
    (48, __('Липецкая область')),
    (49, __('Магаданская область')),
    (50, __('Московская область')),
    (51, __('Мурманская область')),
    (52, __('Нижегородская область')),
    (53, __('Новгородская область')),
    (54, __('Новосибирская область')),
    (55, __('Омская область')),
    (56, __('Оренбургская область')),
    (57, __('Орловская область')),
    (58, __('Пензенская область')),
    (59, __('Пермский край')),
    (60, __('Псковская область')),
    (61, __('Ростовская область')),
    (62, __('Рязанская область')),
    (63, __('Самарская область')),
    (64, __('Саратовская область')),
    (65, __('Сахалинская область')),
    (66, __('Свердловская область')),
    (67, __('Смоленская область')),
    (68, __('Тамбовская область')),
    (69, __('Тверская область')),
    (70, __('Томская область')),
    (71, __('Тульская область')),
    (72, __('Тюменская область')),
    (73, __('Ульяновская область')),
    (74, __('Челябинская область')),
    (75, __('Забайкальский край')),
    (76, __('Ярославская область')),
    (77, __('Москва')),
    (78, __('Санкт-Петербург')),
    (79, __('Еврейская автономная область')),
    (83, __('Ненецкий автономный округ')),
    (86, __('Ханты-Мансийский Автономный округ - Югра')),
    (87, __('Чукотский автономный округ')),
    (89, __('Ямало-Ненецкий автономный округ')),
    (91, __('Республика Крым')),
    (92, __('Севастополь')),
    (99, __('Иные территории, включая город и космодром Байконур')),
)


class LocalityType(Choices):
    LOC_TYPE_1 = 'аал', __('аал')
    LOC_TYPE_2 = 'аул', __('аул')
    LOC_TYPE_3 = 'волость', __('волость')
    LOC_TYPE_4 = 'высел', __('выселки(ок)')
    LOC_TYPE_5 = 'г', __('город')
    LOC_TYPE_6 = 'городок', __('городок')
    LOC_TYPE_7 = 'д', __('деревня')
    LOC_TYPE_8 = 'дп', __('дачный поселок')
    LOC_TYPE_9 = 'ж/д_будка', __('железнодорожная будка')
    LOC_TYPE_10 = 'ж/д_казарм', __('железнодорожная казарма')
    LOC_TYPE_11 = 'ж/д_оп', __('ж/д остановочный (обгонный) пункт')
    LOC_TYPE_12 = 'ж/д_платф', __('железнодорожная платформа')
    LOC_TYPE_13 = 'ж/д_пост', __('железнодорожный пост')
    LOC_TYPE_14 = 'ж/д_рзд', __('железнодорожный разъезд')
    LOC_TYPE_15 = 'ж/д_ст', __('железнодорожная станция')
    LOC_TYPE_16 = 'заимка', __('заимка')
    LOC_TYPE_17 = 'казарма', __('казарма')
    LOC_TYPE_18 = 'кп', __('курортный поселок')
    LOC_TYPE_19 = 'м', __('местечко')
    LOC_TYPE_20 = 'мкр', __('микрорайон')
    LOC_TYPE_21 = 'нп', __('населенный пункт')
    LOC_TYPE_22 = 'остров', __('остров')
    LOC_TYPE_23 = 'п', __('поселок сельского типа')
    LOC_TYPE_24 = 'п/о', __('почтовое отделение')
    LOC_TYPE_25 = 'п/р', __('планировочный район')
    LOC_TYPE_26 = 'п/ст', __('поселок и(при) станция(и)')
    LOC_TYPE_27 = 'пгт', __('поселок городского типа')
    LOC_TYPE_28 = 'починок', __('починок')
    LOC_TYPE_29 = 'промзона', __('промышленная зона')
    LOC_TYPE_30 = 'рзд', __('разъезд')
    LOC_TYPE_31 = 'рп', __('рабочий (заводской) поселок')
    LOC_TYPE_32 = 'с', __('село')
    LOC_TYPE_33 = 'с/а', __('сельская администрация')
    LOC_TYPE_34 = 'с/мо', __('сельское муницип. образование')
    LOC_TYPE_35 = 'с/о', __('сельский округ')
    LOC_TYPE_36 = 'с/пос', __('сельское поселение')
    LOC_TYPE_37 = 'с/с', __('сельсовет')
    LOC_TYPE_38 = 'с/тер', __('сельская территория')
    LOC_TYPE_39 = 'сл', __('слобода')
    LOC_TYPE_40 = 'ст-ца', __('станица')
    LOC_TYPE_41 = 'тер', __('территория')
    LOC_TYPE_42 = 'у', __('улус')
    LOC_TYPE_43 = 'х', __('хутор')
