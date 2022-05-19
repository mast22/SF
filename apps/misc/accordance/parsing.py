"""
Для работы с Accordance заложен следующий процесс:
1. Составляется таблица в Google Docs в которой мы проводим соответсвие различных значений из банков. Это наиболее легкий способ составления, перемещения и управления данными
2. Таблицы сохраняются в формате TSV (разделение через tab) и загружаются в эту папку.
3. Парсер настраивается для обработки данных определенным образом
4. Данные парсятся необходимым образом и сохраняются в БД.

Данные собираются в JSON массив поскольку некоторые банки требуют чтобы для обозначения одного значения требовалось
несколько идентификаторов

Данные разбросаны в TSV и Dict в двух папках
Если после конца списка в TSV остался текст, то его лучше удалить
"""
from typing import Union, List

from apps.banks.const import BankBrand
from apps.misc.const import AccordanceCollection
from apps.misc.models.accordance import Accordance


def save_csv_accordance():
    def get_value_from_row(index: Union[int, List[int]], row: List):
        if isinstance(index, int):
            return row[index]
        return [row[ind] for ind in index]

    industry_path = 'apps/misc/accordance/csv/industry.tsv'
    industry_config = {
        'desc': 1,
        'general': 2,
        'specific': {
            BankBrand.OTP: 3,
            BankBrand.ALFA: 5,
            # BankBrand.MTS: [],
            BankBrand.POCHTA: 7,
        },
    }

    good_category_path = 'apps/misc/accordance/csv/good_category.tsv'
    good_category_config = {
        'desc': 1,
        'general': 2,
        'specific': {
            BankBrand.OTP: 3,
            BankBrand.ALFA: 5,
            # BankBrand.MTS: [],
            BankBrand.POCHTA: [7, 9],
        },
    }

    parse_plan = {
        AccordanceCollection.INDUSTRY: {'path': industry_path, 'config': industry_config},
        AccordanceCollection.GOOD_CATEGORY: {'path': good_category_path, 'config': good_category_config}
    }

    items = []
    for collection, collection_path_config in parse_plan.items():
        with open(collection_path_config['path'], 'r') as file:
            for line in file.readlines()[1:]:
                splited_line = line.split('\t')

                if splited_line[0] == '':
                    # Конец файла
                    break

                # items.append(
                Accordance.objects.create(
                    desc=splited_line[collection_path_config['config']['desc']],
                    specific={
                        BankBrand.OTP: get_value_from_row(collection_path_config['config']['specific'][BankBrand.OTP], splited_line),
                        BankBrand.POCHTA: get_value_from_row(collection_path_config['config']['specific'][BankBrand.POCHTA], splited_line),
                        BankBrand.ALFA: get_value_from_row(collection_path_config['config']['specific'][BankBrand.ALFA], splited_line),
                    },
                    collection=collection,
                    general=splited_line[collection_path_config['config']['general']]
                )
                # )


def save_dict_accordance():
    from apps.misc.accordance.dicts import appearance, org_ownership, position_types, good_services
    items = []

    for item in appearance.APP_ACC:
        items.append(Accordance(
            desc=item['desc'],
            specific=item['specific'],
            collection=AccordanceCollection.APPEARANCE,
            general=item['general'],
        ))

    for item in org_ownership.ORG_OWNERSHIP:
        items.append(Accordance(
            desc=item['desc'],
            specific=item['specific'],
            collection=AccordanceCollection.ORG_OWNERSHIP,
            general=item['general'],
        ))

    for item in position_types.POSITION_TYPE:
        items.append(Accordance(
            desc=item['desc'],
            specific=item['specific'],
            collection=AccordanceCollection.POSITION_TYPE,
            general=item['general'],
        ))

    for item in good_services.GOOD_SERVICES:
        items.append(Accordance(
            desc=item['desc'],
            specific=item['specific'],
            collection=AccordanceCollection.GOOD_SERVICES,
            general=item['general'],
        ))

    Accordance.objects.bulk_create(items)
