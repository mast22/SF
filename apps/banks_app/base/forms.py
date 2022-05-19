from django.conf import settings

from .rules import BaseRule
from apps.misc.models.accordance import Accordance
from apps.orders.models import OrderCreditProduct
from apps.common.utils import generate_random_uuid
from apps.banks.models import AgentBank, OutletBank
from django.db.models import ObjectDoesNotExist
from apps.common.utils import nested_getattr
from typing import Any, Callable, List, Dict, Type
from django.db.models.fields.files import ImageFieldFile
import base64
import pathlib

from apps.partners.models import PartnerBank
from apps.testing.fixtures.data import TEST_AGENT_CODE, TEST_OUTLET_CODE, TEST_PARTNER_CODE


class FormParsingException(Exception):
    pass


possible_form_exceptions = (KeyError, AttributeError, ObjectDoesNotExist, TypeError, FormParsingException)


class BaseBankForm:
    """ Промежуточная модель между заказом СФ и анкетами банков

    Обработка проходит в 2 этапа:
    1. Перевод значений из формата формы в словарь
    2. Удаление лишних элементов по запуску правила `presence`
    base (База) - объект Order или один из дочерних. От базы происходит поиск определённого аттрибута в дереве объектов.
    lookup - строка адреса аттрибута. Отталкивается от базы

    Методы данного класса переписываются и теперь используются производные класса BaseRule
    В будущем необходимо всё перевести
    """
    mapper = {}

    def __init__(self, ocp: OrderCreditProduct, order: 'Order', bank: 'Bank', credit_product: 'CreditProduct'):
        self.ocp = ocp
        self.order = order
        self.bank = bank
        self.credit_product = credit_product
        self.bank_payload = {}
        self.documents = {}

    def get_agent_code(self) -> str:
        if settings.PLUG_MODE:
            return TEST_AGENT_CODE[self.bank.name]
        return AgentBank.objects.get(agent=self.order.agent, bank=self.bank).code

    def get_outlet_code(self) -> str:
        if settings.PLUG_MODE:
            return TEST_OUTLET_CODE[self.bank.name]
        return OutletBank.objects.get(bank=self.bank, outlet=self.order.outlet).code

    def get_partner_code(self) -> str:
        if settings.PLUG_MODE:
            return TEST_PARTNER_CODE[self.bank.name]
        return PartnerBank.objects.get(bank=self.bank, partner=self.order.outlet.partner).code

    def get_product_code(self) -> str:
        return self.credit_product.code

    def get_outlet_address(self) -> str:
        return self.order.outlet.address.to_human()

    @staticmethod
    def convert_enum(base, lookup: str, mapper: dict, default=None) -> Any:
        value = nested_getattr(base, lookup)
        return mapper.get(value, default)

    @staticmethod
    def convert_raw(base, lookup: str) -> Any:
        return nested_getattr(base, lookup)

    @staticmethod
    def convert_transform(base, lookup: str, callable: Callable) -> Any:
        return callable(nested_getattr(base, lookup))

    @staticmethod
    def convert_accordance(base, lookup: str, callable: Callable or None = None):
        result: Accordance = nested_getattr(base, lookup)
        if result is None:
            return None
        # result = result.get_bank_value()
        if callable is not None:
            return callable(result)
        return result

    @staticmethod
    def convert_const(base, value) -> Any:
        return value

    @staticmethod
    def convert_calculated(base, callable: Callable) -> Any:
        return callable(base)

    def convert_method(self, base, method_name, lookup: str or None = None) -> Any:
        """ Выполняет метод формы, в качестве аргумента передаёт указанное название функции и значение из БД  """
        method = getattr(self, method_name)
        if lookup is not None:
            lookup_value = nested_getattr(base, lookup)
            return method(lookup_value)
        return method()

    def convert_dict(self, base: object, data: Dict) -> Dict:
        """ Конвертирует вложенную структуру """
        result = {}
        for key, rule in data.items():
            result[key] = self.exception_wrapper(self._make_conversion, key, base, conversion_rule=rule)

        return result

    def convert_list(self, base, children_name, fields):
        """ Конвертирует аналогично convert_dict, но для структуры списка """
        # Лучше в fields передавать только аргументы, позже можно отрефакторить
        items = {children_name: []}
        for field in fields:
            item = {}
            for rule_name, conversion_rule in field.items():
                item[rule_name] = self.exception_wrapper(
                    self._make_conversion, rule_name, base, conversion_rule=conversion_rule
                )
            items[children_name].append(item)

        return items

    def convert_loop(
            self, base, lookup: str, inner: dict, children_name: str,
            modify_items: str or None = None, other_base: str or None = None,
    ) -> Dict[
        str, List]:
        """ Конвертирует плоскую структуру аналогично convert_list, но в отличии от него
        он использует в качестве основы обратное отношение в БД. Например, список товаров заказа
        """
        items = {children_name: []}
        if other_base:
            base = getattr(self, other_base)
        base = nested_getattr(base, lookup)
        if modify_items is not None:
            modifier_callable = getattr(self, modify_items)
            base = modifier_callable(base)
        if hasattr(base, 'all'):  # Если передан `objects` и нужно достать Queryset
            base = base.all()
        for item in base:
            good = {}
            for key, value in inner.items():
                good[key] = self.exception_wrapper(self._make_conversion, key, item, conversion_rule=value)
            items[children_name].append(good)

        return items

    def convert_process_list(self, base, children_name: str, mapping: Dict, method_name: str):
        method = getattr(self, method_name)
        return {children_name: method(self.order, mapping)}

    @staticmethod
    def cast_filename(value: Type[ImageFieldFile]):
        return generate_random_uuid()

    @staticmethod
    def cast_file_extension(value: Type[ImageFieldFile]):
        return pathlib.Path(value.name).suffix[1:]

    @staticmethod
    def cast_file_base64(value: Type[ImageFieldFile]):
        """ Переводит файл в base64 """
        return base64.b64encode(value.read()) if value else None

    @staticmethod
    def cast_date(value):
        """ Переводит дату в требуемый формат """
        return value.strftime('%m/%d/%Y')

    def _make_conversion(self, base: object, conversion_rule: dict) -> Any:
        if isinstance(conversion_rule, BaseRule):
            return conversion_rule.evaluate()

        new_conversion_rule = conversion_rule.copy()
        # Проверка не производятся во время конвертации
        _ = new_conversion_rule.pop('presence', None)
        _ = new_conversion_rule.pop('proceed', None)

        converter_name = new_conversion_rule.pop('converter')

        converter = getattr(self, converter_name)
        return converter(base, **new_conversion_rule)

    def _remove_not_required_values(self, payload: dict) -> dict:
        """ Удалим излишние значения по выполнению правила presence """
        items_to_remove = []
        for key, value in self.mapper.items():
            if isinstance(value, BaseRule):
                # Временная затычка для использования обоих решения
                # и классов - правил и словарей
                if not value.should_present(payload):
                    items_to_remove.append(key)
                continue

            presence = value.get('presence', None)
            if presence is not None:
                if not presence(payload):
                    items_to_remove.append(key)

        # При итерации по словарю невозможно удалять значения
        for item in items_to_remove:
            try:
                del payload[item]
            except KeyError:
                pass

        return payload

    @staticmethod
    def exception_wrapper(operation: Callable, key: str, *args, **kwargs):
        try:
            result = operation(*args, **kwargs)
        except possible_form_exceptions as e:
            raise FormParsingException(f'Ошибка при обработке {key}: {e}')

        return result

    def convert_order_to_bank_payload(self) -> Dict:
        for key, value in self.mapper.items():
            # proceed - уведомляет нужно ли продолжать конвертацию данного поля
            if isinstance(value, BaseRule):
                # Временная затычка для использования обоих решения
                # и классов - правил и словарей
                value.set_form(self)
                value.set_base(self.order)
                if not value.should_proceed():
                    continue
                self.bank_payload[key] = value.evaluate()
                continue

            proceed = value.get('proceed', None)
            if proceed and not proceed(self.order):
                continue

            self.bank_payload[key] = self.exception_wrapper(
                self._make_conversion, key, self.order, conversion_rule=value
            )

        # Удаление элементов происходит на том же уровне вложенности на котором этот элемент расположен
        self.bank_payload = self._remove_not_required_values(self.bank_payload)
        return self.bank_payload

    def set_documents(self, documents: List[Dict[str, str]]):
        """ Прикрепляет документы к форме
        Формат: {
            'name': <str: имя документа>,
            'type': <str enum: тип документа, принимаемого otp>,
            'ext': <str: расширение документа: (xlsx, pdf, png)>,
            'buffer': <str: base64 строка файла> # использовать единый формат передачи файла
        }

        Типы документов ОТП:
        Фотография
        Заявление-анкета
        Индивидуальные условия
        Паспорт гражданина РФ
        Согласие на страхование
        Согласие на обработку данных
        Заявление об изменении данных
        Заявление-оферта
        Соглашение ЭП (МФО)
        Соглашение ЭП (Банк)
        """
        self.documents = documents

    def convert_attached(self, base, children_name, patterns):
        """ Добавляет прикрепленные документы к форме
        использует все прикрепленные файлы через set_documents
        """
        items = {children_name: []}
        for doc in self.documents:
            for pattern in patterns:
                items[children_name].append({pattern['name']: doc[pattern['key']]})

        return items
