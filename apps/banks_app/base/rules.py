from typing import Callable, Optional, Any, Dict, List

#from apps.common.models import Model
from apps.misc.models.accordance import Accordance


class BaseRule:
    form: 'BaseBankForm'
    base: Optional['Model'] = None
    presence: Optional[Callable] = None
    proceed: Optional[Callable] = None

    def evaluate(self) -> Any:
        raise NotImplementedError()

    def should_present(self, payload: Dict):
        if self.presence is not None:
            return self.presence(payload)
        return True

    def should_proceed(self):
        if self.proceed is not None:
            return self.proceed(self.base)
        return True

    def nested_getattr(self, lookup: str, obj: Optional[object] = None):
        """ Вложенный getattr, по умолчанию в качестве базы используется Order """
        if obj is None:
            obj = self.base
        for level in lookup.split('.'):
            obj = getattr(obj, level)

        return obj

    def set_form(self, form: "BaseBankForm") -> "BaseRule":
        """ Методы к которым мы обращаемся находятся на классе формы """
        self.form = form

        return self

    def set_base(self, order: "Order") -> "BaseRule":
        """ Установка базы (заказа) необходимо для конфигурации и смены базы """
        self.base = order

        return self

    def set_base_and_form(self, order: "Order", form: "BaseBankForm"):
        """ Shortcut for set_base and set_form """
        self.form = form
        self.base = order

        return self

    # fluent interface pattern
    def with_presence(self, func: Optional[Callable] = None):
        """ В функцию передаётся payload для определения необходимости удаления значения из payload
        Пример: RawRule('career_education.months_of_exp')
            .with_presence(lambda payload: payload['Worker_flg'] == 'Y')
        Если значение `Worker_flg` == 'Y' то оставляем значение, иначе удаляем
        Невозможно использовать для вложенных структур, то для корневых т.е. теми, которые являются ключами mapper
        """
        self.presence = func
        return self

    def with_proceed(self, func: Optional[Callable] = None):
        """ В функцию передаётся base для определения нужно ли вычислить данное значение
        Пример: RawRule('extra_data.previous_last_name').with_proceed(
                lambda base: base.extra_data.previous_last_name is not None)
        Если значение "Предыдущая фамилия не None" то добавить его в значения
        Предпочтительнее чем with_presence потому что решение о добавлении в payload применяется при вычислении значения
        """
        self.proceed = func
        return self


class MethodRule(BaseRule):
    """ Выполняет метод, который определен на классе формы """
    method_name: str
    lookup: Optional[str]

    def __init__(self, method_name: str, lookup: Optional[str] = None):
        self.method_name = method_name
        self.lookup = lookup

    def evaluate(self) -> Any:
        args = {}
        if self.lookup is not None:
            value = self.nested_getattr(self.lookup)
            args['value'] = value
        return getattr(self.form, self.method_name)(**args)


class ConstRule(BaseRule):
    """ Возвращает тоже самое значение """

    def __init__(self, value: Any):
        self.value = value

    def evaluate(self):
        return self.value


class RawRule(BaseRule):
    """ Берет значение прямиком из БД без изменений """

    def __init__(self, lookup: str):
        self.lookup = lookup

    def evaluate(self):
        return self.nested_getattr(self.lookup)


class TransformRule(BaseRule):
    """ Передаваемая функция используется на полученное значение из БД """
    func: Callable

    def __init__(self, lookup: str, func: Callable):
        self.lookup = lookup
        self.callable = func

    def evaluate(self) -> Any:
        return self.callable(self.nested_getattr(self.lookup))


class EnumRule(BaseRule):
    """ Значение полученное из БД используется в качестве ключа для mapper """
    mapper: Dict
    default: Optional[Any]

    def __init__(self, lookup: str, mapper: Dict, default: Optional[Any] = None):
        self.lookup = lookup
        self.mapper = mapper
        self.default = default

    def evaluate(self) -> Any:
        value = self.nested_getattr(self.lookup)
        return self.mapper.get(value, self.default)


class CalculatedRule(BaseRule):
    """ Для функции передаётся base для самостоятельного вычисления значения """
    func: Callable

    def __init__(self, func: Callable):
        self.func = func

    def evaluate(self) -> Any:
        return self.func(self.base)


class AccordanceRule(BaseRule):
    """ Работает аналогично RawRule, но дополнительно изменяет значение для подстановки в систему банка
    В func иногда передаётся лямбда для изъятия значения из массива, возвращаемого данным классом.
    Это происходит если банк требует несколько значений для передачи в их систему
    Более элегантную систему я ещё не придумал, да и времени для этого нет.
    """
    specifier: str
    func: Callable

    def __init__(self, lookup: str, func: Optional[Callable] = None):
        self.lookup = lookup
        self.func = func

    def evaluate(self):
        result: Accordance = self.nested_getattr(self.lookup)
        if result is None:
            return None
        result = result.get_bank_value(self.form.bank.name)
        if self.func is not None:
            return self.func(result)
        return result


class LoopRule(BaseRule):
    """ Используется когда в качестве базы необходимо использовать Queryset
    Результатом выполнения является список элементов, каждый из которых был использован в качестве базы
    для всех указаны правил.
    Пример
    Правило: { 'outer': LoopRule(lookup='goods', inner={'good_name': ConstRule('Name')}, children_name='ChildrenName') }
    Результат: { 'outer': {'ChildrenName': [{'good_name': 'Name'}, ...]} }
    """
    children_name: str
    modify_items_func: Optional[Callable] = None

    def __init__(self, lookup: str, inner: dict, children_name: str):
        self.lookup = lookup
        self.inner = inner
        self.children_name = children_name

    def evaluate(self) -> Dict[str, Any]:
        items = {self.children_name: []}
        self.set_base(self.nested_getattr(lookup=self.lookup))
        if self.modify_items_func is not None:
            self.base = self.modify_items_func(self.base)
        if hasattr(self.base, 'all'):  # Если передан `objects` и нужно достать Queryset
            self.base = self.base.all()
        for item in self.base:
            processed_inner = {}
            for key, rule in self.inner.items():
                # Предоставляем правилу доступ к внешним элементам
                rule: BaseRule = rule.set_base(item)
                rule = rule.set_form(self.form)
                processed_inner[key] = rule.evaluate()
            items[self.children_name].append(processed_inner)

        return items

    def with_ocp_base(self):
        """ В качестве базы используется OCP в объекте формы """
        self.base = self.form.ocp
        return self

    def with_modify_items_method(self, func: Callable):
        """ Метод формы используется для модифицирования элементов """
        self.modify_items_func = func
        return self


class ListRule(BaseRule):
    children_name: str
    fields: List[Dict[str, BaseRule]]

    def __init__(self, children_name: str, fields: List[Dict[str, BaseRule]]):
        self.children_name = children_name
        self.fields = fields

    def evaluate(self) -> Any:
        items = {self.children_name: []}
        for field in self.fields:
            item = {}
            for name, rule in field.items():
                rule.set_base_and_form(self.base, self.form)
                item[name] = rule.evaluate()
            items[self.children_name].append(item)

        return items


class DictRule(BaseRule):
    data: Dict

    def __init__(self, data: Dict):
        self.data = data

    def evaluate(self) -> Any:
        result = {}
        for key, rule in self.data.items():
            rule.set_base_and_form(self.base, self.form)
            result[key] = rule.evaluate()

        return result
