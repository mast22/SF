import random
import string
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from apps.partners.models import Location
from apps.partners.const import LocalityType
from apps.banks.const import BankBrand

TEST_CREDIT_PRODUCT_CODE = {
    BankBrand.OTP: 'PKP239_M8_24',
    BankBrand.POCHTA: '-POCHTA-',
    BankBrand.ALFA: '-ALFA-',
    BankBrand.MTS: '-MTS-',
}

TEST_OUTLET_CODE = {
    BankBrand.OTP: '3632',
    BankBrand.POCHTA: '3632',
    BankBrand.ALFA: '3632',
    BankBrand.MTS: '3632',
}

TEST_AGENT_CODE = {
    BankBrand.OTP: '004451320751512813',
    BankBrand.POCHTA: '000',
    BankBrand.ALFA: '000',
    BankBrand.MTS: '000',
}

TEST_PARTNER_CODE = {
    BankBrand.OTP: '008',
    BankBrand.POCHTA: '000',
    BankBrand.ALFA: '000',
    BankBrand.MTS: '000',
}

first_names = [
    'Михаил', 'Николай', 'Виталий', 'Инакентий', 'Варфоломей', 'Лука',
    'Сергей', 'Борис', 'Тимур', 'Григорий', 'Дмитрий', 'Валентин', 'Владимир',
    'Ахмед', 'Александр', 'Святослав', 'Тихомир',
    'Ярополк', 'Всеволод', 'Богдан', 'Фидель', 'Иосиф',
]
last_names = [
    'Смирнов', 'Иванов', 'Кузнецов', 'Соколов', 'Попов', 'Лебедев', 'Козлов', 'Новиков', 'Морозов',
    'Петров', 'Волков', 'Соловьёв', 'Васильев', 'Зайцев', 'Павлов', 'Семёнов', 'Голубев', 'Виноградов',
    'Богданов', 'Воробьёв', 'Фёдоров', 'Михайлов', 'Беляев', 'Тарасов', 'Белов', 'Комаров', 'Орлов',
    'Киселёв', 'Макаров', 'Андреев', 'Ковалёв', 'Ильин', 'Гусев', 'Титов', 'Кузьмин', 'Кудрявцев',
    'Баранов', 'Куликов', 'Алексеев', 'Степанов', 'Яковлев', 'Сорокин', 'Сергеев', 'Романов', 'Захаров',
    'Борисов', 'Королёв', 'Герасимов', 'Пономарёв', 'Григорьев', 'Лазарев', 'Медведев', 'Ершов', 'Никитин',
    'Соболев', 'Рябов', 'Поляков', 'Цветков', 'Данилов', 'Жуков', 'Фролов', 'Журавлёв', 'Николаев', 'Крылов',
    'Максимов', 'Сидоров', 'Осипов', 'Белоусов', 'Федотов', 'Дорофеев', 'Егоров', 'Матвеев', 'Бобров', 'Дмитриев',
    'Калинин', 'Анисимов', 'Петухов', 'Антонов',
]
streets = ['Ленина', 'Социалистическая', 'Комсомольская', 'Карла Маркса', 'Победы']


def get_random_company_name() -> str:
    first_part = ['ООО', 'ЗАО', 'ИП']
    second_part = ['Кам', 'Волга', 'Казань']
    third_part = ['Орг', 'Строй', 'Бур', 'Нефте']
    forth_part = ['Синтез', 'Консалтинг', 'Инвест']

    return f'{random.choice(first_part)} ' \
           f'{random.choice(second_part)}' \
           f'{random.choice(third_part)}' \
           f'{random.choice(forth_part)}'


def get_random_int_string(n) -> str:
    return str(random.randint(0, (10**n - 1))).zfill(n)


def get_random_birth_date() -> datetime:
    # Дата рождения рассчитывается следующим образом чтобы
    # Датой получения паспорта можно было указать следующий день после исполнения 21 года
    cur_moment = datetime.now()
    start = cur_moment - relativedelta(years=43)
    end = cur_moment - relativedelta(years=22)
    return get_random_date_between(start, end)


def get_random_date_between(start, end):
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randint(0, int_delta)
    return start + timedelta(seconds=random_second)


def get_random_date() -> datetime:
    d = random.randint(0, int(time.time()))
    return datetime.fromtimestamp(d)


def get_random_string(n=8) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))


def generate_random_email() -> str:
    return f'{get_random_string()}@mail.com'


def get_random_phone() -> str:
    return f'+79{get_random_int_string(9)}'


def get_random_last_name() -> str:
    return random.choice(last_names)


def get_random_first_name() -> str:
    return random.choice(first_names)


password = 'servfins'

locations = [
    {
        'street': 'Поперечно-Базарная',
        'house': '72',
        'locality': 'Казань',
        'subject': 16,
        'postcode': '420032',
        'type': LocalityType.LOC_TYPE_5
    }
]


def get_random_location() -> Location:
    # region = list(dict(REGION_CHOICES).keys())
    # loc = Location.objects.create(
    #     street=random.choice(streets),
    #     house=str(random.randint(1, 100)),
    #     locality=get_random_string(),
    #     subject=random.choice(region),
    #     postcode=random.choice(['127642']),
    # )
    loc = Location.objects.create(**random.choice(locations))

    return loc


def get_random_ip() -> str:
    return ".".join(str(random.randint(0, 255)) for _ in range(4))
