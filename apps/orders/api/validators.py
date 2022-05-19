from rest_framework_json_api import serializers as s
from datetime import date

error_string = 'Введенное значение {value} запрещено'


def check_forbidden_words(value: str):
    # TODO доделать валидацию, не все случаи продуманы

    forbidden = (
        '*', '=', '!', '?', ';', '#', '_', '%', '&', '@', '<', '>', '^', '$', '{}', '[]', '[', ']', '{', '}', '~',
        '`', '+', 'НЕТ', 'ФЫВА', 'ТЕСТ', 'ОТСУТСТВУЕТ', 'ОШИБКА', 'НЕИЗВЕСТНО', 'НЕ ИЗВЕСТНО', 'НЕТ ДАННЫХ', 'Н/Д',
        'ДАННЫЕ ОТСУТСТВУЮТ', 'ПУСТО', 'NOT', 'NA', 'N/A', 'NONE', 'TEST', 'MISSING', 'ERROR', 'NO DATA',
        'NOT SUPPLIED', 'NOT PROVIDED', '000000', '-', '–', ' ',
    )

    value = value.upper()

    for forb_val in forbidden:
        value = value.replace(forb_val, '')

    if value == '':
        raise s.ValidationError(f'Введенное значение {value} запрещено')
