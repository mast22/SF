import importlib
from typing import List, Tuple, Sequence, Mapping

from django.core.exceptions import EmptyResultSet
from apps.common.utils import is_iterable
from django.conf import settings
from django.db.models import Q, QuerySet, Model, Subquery
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission, BasePermissionMetaclass
from rest_framework.filters import BaseFilterBackend
from .const import UserMethodTuple, NormalizedMethodTuple, SAFE_METHODS


class BaseAccessPolicyMetaclass(BasePermissionMetaclass, type):
    """Metaclass to normalize all rules."""
    @classmethod
    def normalize_rules(msc, rules: Sequence, class_name: str, bases: Sequence, attrs: Mapping) -> Tuple[dict]:
        for rule in rules:
            for elem in (
                'actions',
                'roles',
                'type',
                'permissions',
                'object_permissions',
                'conditions',
                'queryset_filters',
                'principals',
            ):
                entry = rule.get(elem, None)
                if not entry:
                    rule[elem] = tuple()
                elif is_iterable(entry) and not isinstance(entry, UserMethodTuple):
                    rule[elem] = tuple(entry)
                else:
                    rule[elem] = (entry,)

            try:
                rule['roles'] = set(rule['roles'])
            except Exception as err:
                print('Error:', err, 'Rule:', rule, 'for class:', class_name)
                raise

            for elem in ('conditions', 'queryset_filters'):
                normalized_methods = []
                for method in rule[elem]:
                    if isinstance(method, str):
                        normalized_method = msc._get_normalized_method(method, class_name, bases, attrs)
                    elif isinstance(method, UserMethodTuple):
                        method_real = msc._get_method(method.name, class_name, bases, attrs)
                        normalized_method = NormalizedMethodTuple(method_real, method.args, method.kwargs)
                    elif isinstance(method, NormalizedMethodTuple):
                        normalized_method = method
                    else:
                        raise ValueError(f'Wrong method: {method} in elem: {elem} of rule: {rule} for {class_name}')
                    normalized_methods.append(normalized_method)
                rule[elem] = tuple(normalized_methods)

            if 'effect' not in rule:
                rule['effect'] = None
            assert(rule['effect']) in ('allow', 'deny', None), \
                'Effect should be one of "allow" or "deny" or empty, got: {}'.format(rule['effect'])

        return tuple(rules)

    @classmethod
    def _get_normalized_method(msc, method_str: str, class_name, bases, attrs):
        parts = method_str.split(':', 1)
        method = msc._get_method(parts[0], class_name, bases, attrs)
        args, kwargs = msc._get_method_arguments(parts[1] if len(parts) == 2 else None)
        return NormalizedMethodTuple(method, args, kwargs)

    @staticmethod
    def _get_method(method_name: str, class_name, bases, attrs):
        if method_name in attrs:
            method = attrs[method_name]
            if isinstance(method, staticmethod):
                return method.__func__
            return attrs[method_name]

        for base_class in bases:
            method = getattr(base_class, method_name, None)
            if method is not None:
                return method

        if hasattr(settings, 'PERMISSIONS_SETTINGS'):
            module_path = settings.PERMISSIONS_SETTINGS.get('reusable_conditions', None)
            if module_path:
                module = importlib.import_module(module_path)

                if hasattr(module, method_name):
                    return getattr(module, method_name)

        assert False, f'condition "{method_name}" must be a method on the access policy ' \
                      f'or be defined in the "reusable_conditions" module. Class: {class_name}'

    @staticmethod
    def _get_method_arguments(method_arguments):
        args, kwargs = [], {}
        if method_arguments:
            args_list = method_arguments.split(',')
            for arg in args_list:
                arg = arg.strip()
                if '=' in arg:
                    name, value = arg.split('=', 1)
                    name = name.strip()
                    value = value.strip()
                    if name:
                        kwargs[name] = value
                else:
                    args.append(arg)
        return args, kwargs

    def __new__(mcs, name, bases, attrs):
        attrs['rules'] = mcs.normalize_rules(attrs.get('rules', tuple()), name, bases, attrs)
        return super().__new__(mcs, name, bases, attrs)



class BaseAccessPolicy(BaseFilterBackend, BasePermission, metaclass=BaseAccessPolicyMetaclass):
    """Базовый класс для проверки прав доступа в виде набора правил."""
    rules = tuple()

    # Отладка принтами - иногда пригождается для тестов прав, т.к. отладка тестов работает очень медленно
    print_log = getattr(settings, 'PERMISSIONS_SETTINGS', {}).get('print_log', True)

    # Стандартные права для HTTP-методов, взято из DjangoModelPermissions, с некоторыми изменениями
    permissions_by_http_method = {
        'GET': ('{app_label}.view_{model_name}',),
        'OPTIONS': ('{app_label}.view_{model_name}',),
        'HEAD': ('{app_label}.view_{model_name}',),
        'POST': ('{app_label}.add_{model_name}',),
        'PUT': ('{app_label}.change_{model_name}',),
        'PATCH': ('{app_label}.change_{model_name}',),
        'DELETE': ('{app_label}.delete_{model_name}',),
    }

    # Может быть прописан в дочернем классе при необходимости, аналогично self.permissions_by_http_method
    rest_actions = {'metadata', 'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy'}
    # Права по текущему action
    permissions_by_action = {}

    # Сообщение запросе действия, на которое недостаточно прав:
    message = _('У вас недостаточно прав для данного действия')

    # Использовать object-level методы для проверки прав доступа
    use_object_permissions = False

    allow_anonymous_access = False

    # Вынести фильтры прав доступа в подзапрос для оптимизации
    filter_as_subquery = False

    # Actions, по которым необходима проверка отдельных полей
    actions_to_check_fields = ('create', 'update', 'partial_update')
    # Default organization lookup for each subclass
    organization_lookup = '<self>'

    def __init__(self, *args, **kwargs):
        self._action = None
        self._method = None

    def filter_queryset(self, request, queryset, view, action=None, method=None) -> QuerySet:
        """Возвращает queryset, отфильтрованный по подходящим правилам (rules, имеющие queryset_filters)."""
        if request.user and request.user.is_superuser:
            return queryset
        action = action if action is not None else self._get_invoked_action(view, request)
        if self.print_log:
            print('=== Queryset filtering. Action:', action)
        self.action = action
        self._method = method
        if action is None:
            return queryset
        return self._evaluate_filtering_rules(self.rules, request, queryset, view, action)

    def has_permission(self, request, view) -> bool:
        user = getattr(request, 'user', None)
        if (user and user.is_superuser) or getattr(view, '_ignore_model_permissions', False):
            return True
        if (not self.allow_anonymous_access) and (not user or user.is_anonymous):
            return False
        action = self._get_invoked_action(view, request)
        if self.print_log:
            print('=== Module Permissions checking. Action:', action)
        if len(self.rules) == 0 or action is None:
            return True
        return self._evaluate_module_checking_rules(self.rules, request, view, action)

    def has_object_permission(self, request, view, obj) -> bool:
        if request.user and request.user.is_superuser:
            return True
        action = self._get_invoked_action(view, request)
        if self.print_log:
            print('=== Object Permissions checking. Action:', action)
        if len(self.rules) == 0 or action is None:
            return False
        return self._evaluate_object_checking_rules(self.rules, request, view, obj, action)

    def _get_invoked_action(self, view, request) -> str:
        """If a CBV, the name of the method. If a regular function view, the name of the function."""
        if self._action:
            return self._action
        if hasattr(view, 'action'):
            if view.action is None and hasattr(view, 'action_map'):
                method = request.method.lower()
                action = view.action_map.get(method, None)
            else:
                action = view.action
        elif hasattr(view, '__class__'):
            action = view.__class__.__name__
        else:
            raise ValueError(f'Could not determine action of request "{request}" on view "{view}"')
        return action

    def _evaluate_module_checking_rules(self, rules, request, view, action) -> bool:
        matched = rules
        matched = self._get_rules_matching_actions(matched, None, request, view, action)
        matched = self._get_rules_matching_types(matched, 'module_level')
        matched = self._get_rules_matching_roles(matched, None, request, view, action)
        matched = self._get_rules_matching_permissions(matched, None, request, view, action)
        matched = self._get_rules_matching_principals(matched, None, request, view, action)
        matched = self._get_rules_matching_conditions(matched, None, request, view, action)
        matched = list(matched)

        allowed = False
        for rule in matched:
            if rule['effect'] == 'allow':
                allowed = True
            elif rule['effect'] == 'deny':
                allowed = False
                break

        if self.print_log:
            denied = [True for rule in matched if rule['effect'] == 'deny']
            allowed2 = [True for rule in matched if rule['effect'] == 'allow']
            print('\n=== Module Permissions checking. Matched:', matched, 'Allow:', allowed2, 'Deny:', denied)
            print(f'User: {request.user}, Role: {request.user.role} action: {action}\n')

        return allowed

    def _evaluate_object_checking_rules(self, rules, request, view, obj, action) -> bool:
        matched = rules
        matched = self._get_rules_matching_actions(matched, obj, request, view, action)
        matched = self._get_rules_matching_types(matched, 'object_level')
        matched = self._get_rules_matching_roles(matched, obj, request, view, action)
        matched = self._get_rules_matching_principals(matched, obj, request, view, action)
        matched = self._get_rules_matching_object_permissions(matched, obj, request, view, action)
        matched = self._get_rules_matching_conditions(matched, obj, request, view, action)
        matched = list(matched)

        # NOTE: Для object_permissions по умолч. возвращаем True, т.к. module-level уже проверены
        allowed = True if request.method in SAFE_METHODS else False
        for rule in matched:
            if rule['effect'] == 'allow':
                allowed = True
            elif rule['effect'] == 'deny':
                allowed = False
                break

        denied = [True for rule in matched if rule['effect'] == 'deny']
        allowed2 = [True for rule in matched if rule['effect'] == 'allow']
        if self.print_log:
            print('\n=== Object Permissions checking. Matched:', matched, 'Allow:', allowed2, 'Deny:', denied)
            print('User:', request.user, 'action:', action, '\n')

        return allowed

    def _evaluate_filtering_rules(self, rules, request, queryset, view, action) -> QuerySet:
        matched = rules
        matched = self._get_rules_matching_actions(matched, queryset, request, view, action)
        matched = self._get_rules_matching_types(matched, 'queryset_filter')
        matched = self._get_rules_matching_roles(matched, queryset, request, view, action)
        matched = self._get_rules_matching_principals(matched, queryset, request, view, action)
        matched = self._get_rules_matching_permissions(matched, queryset, request, view, action)
        matched = self._get_rules_matching_queryset_filters(matched, queryset, request, view, action)
        matched = list(matched) # По filtered_iterable, возвращённому из фильтров можно пробежать всего 1 раз.

        if self.print_log:
            print('\n=== Filtering. Matched:', matched)

        # Теперь имеем список правил, подходящих под наши условия.
        filtered_query = Q(pk__in=[])

        clean_queryset = self._get_model_class(queryset, view).objects.all()
        new_queryset = clean_queryset.none().values('pk')
        filtered_querysets = []

        for rule in matched:
            for qs_filter in rule['queryset_filters']:
                method, args, kwargs = qs_filter
                filtered_queryset = method(self, clean_queryset, request, view, action, *args, **kwargs)
                if filtered_queryset is None:
                    continue
                elif isinstance(filtered_queryset, QuerySet):
                    filtered_querysets.append(filtered_queryset.values('pk'))
                else:
                    raise AttributeError(f'Wrong filtered queryset: {filtered_queryset}.'
                                         ' It needs to be a QuerySet instance or None')
        new_queryset = new_queryset.union(*filtered_querysets)

        pks_subquery = Subquery(new_queryset.values('pk'))
        queryset = queryset.filter(pk__in=pks_subquery)

        if self.print_log:
            print(f'User: {request.user}, Role: {request.user.role},  action: {action}\n')
            print('Filtered queryset:', list(queryset))
            try:
                print('Query:', str(queryset.query))
            except EmptyResultSet:
                print('Query is broken, Fuck the django!')

        return queryset

    @staticmethod
    def _get_rules_matching_types(matched, type):
        def type_filter(rule):
            types = rule['type']
            return bool(not types or '*' in types or type in types)

        return filter(type_filter, matched)

    def _call_queryset_filter(self, qs_filter, queryset, request, view, action):
        method, args, kwargs = qs_filter
        return method(self, queryset, request, view, action, *args, **kwargs)

    @staticmethod
    def _get_rules_matching_queryset_filters(matched, queryset, request, view, action):
        """Фильтрует только правила, в которых присутстует queryset_filters"""
        def has_queryset_filters(rule):
            return len(rule['queryset_filters']) > 0
        return filter(has_queryset_filters, matched)

    def _get_rules_matching_actions(self, matched, obj_or_qs, request, view, action):
        """Фильтрует правила по списку actions.
        Правило применяется если подходит ХОТЯ БЫ ОДНО условие.
        Элементы списка actions могут принимать значения:
        '*' или None - правило действует для любых запросов
        '<safe_methods> - .. если request.Method входит в список SAFE_METHODS ('HEAD', 'OPTIONS', 'GET')
        '<unsafe_methods> - .. если request.Method не из списка SAFE_METHODS
        'list', 'retrieve', 'create', 'update', 'destroy' - один из методов rest-framework-а
        'my_custom_method' - кастомный метод, зарегестрированный во ViewSets
        """
        def rules_filter(rule):
            rule_actions = rule['actions']
            if not rule_actions:
                return True
            if '*' in rule_actions or action in rule_actions:
                return True
            method = self._method if self._method else request.method
            method_is_safe = method in SAFE_METHODS
            if '<safe_methods>' in rule_actions and method_is_safe:
                return True
            if '<unsafe_methods>' in rule_actions and not method_is_safe:
                return True
            if '<rest_actions>' in rule_actions and action in self.rest_actions:
                return True
            return False

        return filter(rules_filter, matched)

    @staticmethod
    def _get_rules_matching_roles(matched, obj_or_qs, request, view, action):
        """Фильтрует правила по списку roles
        Правило применяется если у юзера есть хотя бы одна из ролей из списка где-либо
        """
        current_role = request.user.role

        def role_filter(rule):
            rule_roles = rule['roles']
            if not rule_roles or '*' in rule_roles:
                return True
            if current_role in rule_roles:
                return True
            return False

        return filter(role_filter, matched)

    @staticmethod
    def _get_rules_matching_principals(matched, obj_or_qs, request, view, action):
        """Фильтрует правила по списку principals.
        Правило применяется если подходит ХОТЯ БЫ ОДНО условие.
        Элементы списка principals могут принимать значения:
        '*' или None - правило подходит для всех пользователей
        <is_authenticated> - .. для авторизованных пользователей
        <is_anonymous> - .. для анонимных пользователей
        user:123 - .. для пользователя с id=123
        group:42 - .. для пользователей в группе с id=42
        role:13 - .. для пользователей, с присвоенной группе ролью 13
        Пример:
            'principals': ['role:1', 'group:5, 'user:1']
        """
        user = request.user

        def principal_filter(rule):
            rule_principals = rule['principals']
            if not rule_principals or '*' in rule_principals:
                return True
            if '<is_authenticated>' in rule_principals and user.is_authenticated:
                return True
            if '<is_anonymous>' in rule_principals and user.is_anonymous:
                return True

            principals_users = set()
            principals_groups = set()
            principals_roles = set()

            for p in rule_principals:
                if ':' in p:
                    predicat, p_id = p.split(':')
                    p_id = int(p_id)
                    if predicat == 'user':
                        principals_users.add(p_id)
                    elif predicat == 'group':
                        principals_groups.add(p_id)
                    elif predicat == 'role':
                        principals_roles.add(p_id)

            if principals_users and user.id in principals_users:
                return True
            if principals_groups or principals_roles:
                user_groups = user.groups.all()
                for group in user_groups:
                    if principals_groups and group.id in principals_groups:
                        return True
                    if principals_roles and group.role in principals_roles:
                        return True
            return False

        return filter(principal_filter, matched)

    def _get_rules_matching_permissions(self, matched, queryset, request, view, action):
        """Фильтрует правила по списку permissions, которыми должен обладать пользователь.
        Правило применяется если пользователь имеет ХОТЯ БЫ одно permission из списка.
        Элементы списка principals могут принимать значения:
        '*' или None (отсутствует) - правило действует независимо от прав доступа пользователя.
        <by_action> - берём из словаря self.permissions_by_action
        <by_http_method> - берём из словаря self.permissions_by_http_method
        'app.<CRUD>_object' - разделяется на 'add_object', 'view_object', 'change_object', 'delete_object'
        'add_object', 'view_object', 'change_object', 'delete_object' - стандартные правила, задаваемые в Django.
        """
        user = request.user

        def permissions_filter(rule):
            rule_permissions = rule['permissions']
            result = False
            if not rule_permissions or '*' in rule_permissions:
                return True
            if '<by_action>' in rule_permissions:
                perms_by_action = self._get_action_based_permissions(action, user, view, queryset)
                result = result or any(user.has_perm(perm) for perm in perms_by_action)
            if '<by_http_method>' in rule_permissions:
                perms_by_http = self._get_http_method_based_permissions(request, view, queryset)
                result = result or any(user.has_perm(perm) for perm in perms_by_http)

            result = result or any(user.has_perm(perm) for perm in rule_permissions
                    if perm not in ('<by_action>', '<by_http_method>'))
            return result

        return filter(permissions_filter, matched)

    def _get_rules_matching_object_permissions(self, matched, obj, request, view, action):
        """Фильтрует правила по списку permissions, которыми должен обладать пользователь.
        Правило применяется если пользователь имеет ХОТЯ БЫ одно permission из списка.
        Элементы списка principals могут принимать значения:
        '*' или None (отсутствует) - правило действует независимо от прав доступа пользователя.
        <by_action> - берём из словаря self.permissions_by_action
        <by_http_method> - берём из словаря self.permissions_by_http_method
        'app.<CRUD>_object' - разделяется на 'add_object', 'view_object', 'change_object', 'delete_object'
        'add_object', 'view_object', 'change_object', 'delete_object' - стандартные правила, задаваемые в Django.
        """
        user = request.user
        if not self.use_object_permissions:
            obj = None

        def permissions_filter(rule):
            rule_permissions = rule['object_permissions']
            result = False
            if not rule_permissions or '*' in rule_permissions:
                return True
            if '<by_action>' in rule_permissions:
                perms_by_action = self._get_action_based_permissions(action, user, view, obj)
                result = result or any(user.has_perm(perm, obj) for perm in perms_by_action)
            if '<by_http_method>' in rule_permissions:
                perms_by_http = self._get_http_method_based_permissions(request, view, obj)
                result = result or any(user.has_perm(perm, obj) for perm in perms_by_http)

            result = result or any(user.has_perm(perm, obj) for perm in rule_permissions
                    if perm not in ('<by_action>', '<by_http_method>'))
            return result

        return filter(permissions_filter, matched)

    def _get_action_based_permissions(self, action, user, view, obj_or_qs=None):
        perm_strings = self.permissions_by_action.get(action, None)
        if perm_strings:
            model_class = self._get_model_class(obj_or_qs, view)
            return tuple(perm_str.format(
                app_label=model_class._meta.app_label,
                model_name=model_class._meta.model_name,
            ) for perm_str in perm_strings)
        return tuple()

    def _get_http_method_based_permissions(self, request, view, obj_or_qs=None):
        method = self._method if self._method else request.method
        perm_strings = self.permissions_by_http_method.get(method, None)
        if perm_strings:
            model_class = self._get_model_class(obj_or_qs, view)
            return tuple(perm_str.format(
                app_label=model_class._meta.app_label,
                model_name=model_class._meta.model_name,
            ) for perm_str in perm_strings)
        return tuple()

    @staticmethod
    def _get_model_class(obj_or_qs, view):
        """Получает класс модели из обьекта или из view, если обьект отсутствует"""
        if obj_or_qs is not None:
            if isinstance(obj_or_qs, Model):
                return obj_or_qs.__class__
            elif isinstance(obj_or_qs, QuerySet):
                return obj_or_qs.model
        elif view:
            if hasattr(view, 'get_custom_queryset'):
                return view.get_custom_queryset().model
            elif hasattr(view, 'queryset'):
                return view.queryset.model
        raise ValueError('Got wrong view or object or queryset: {0}, {1}'.format(obj_or_qs, view))

    def _get_rules_matching_conditions(self, matched, obj_or_qs, request, view, action):
        """
        Фильтрует правила по списку conditions - функции, задаваемые пользователем.
        Если action=allow, правило применяется, если прошли ВСЕ проверки.
        Если action=deny, правило применяется, если прошла ХОТЯ БЫ ОДНА проверка.
        Элементы списка conditions могут принимать следующие значения:
        '*' или None (отсутствует) - правило действует независимо от кастомных условий.
        'method_name' - проверяется self.method_name
            или ищутся в файле: {django.conf.settings.PERMISSIONS_SETTINGS}.reusable_conditions
            метод должен иметь следующую сигнатуру:
                def method_name(obj_or_qs, request, view, action, *args, **kwargs) -> bool
            где:
                obj_or_qs - обьект или queryset, для которого проверяется доступ.
                request - текущий request
                view - ссылка на view (ModelViewSet), для которого проверяется доступ.
                    Нельзя вызывать метод view.get_object() - приведёт к рекурсивному запросу, т.к. проверка
                    прав вызывается внутри этого метода!
                action - строка, название метода ModelViewSet или функции, в которой проходит проверка прав
        Возможно передавать набор параметров для кастомизации:
        'check_some:arg1,arg2,kwarg1=1,kwarg2=2' - метод check_some будет вызван следующим образом:
                check_some(obj_or_qs, condition: str, request, view, action, arg1, arg2, kwarg1=1, kwarg2=2)
        checker должен вернуть bool либо None (правило игнорируется)
        """

        def condition_filter(rule):
            rule_conditions = rule['conditions']
            effect = rule['effect']
            if not rule_conditions or '*' in rule_conditions:
                return True
            for condition in rule_conditions:
                method, args, kwargs = condition
                result = method(self, obj_or_qs, request, view, action, *args, **kwargs)
                if result is None:
                    # Если checker вернул None - игнорирую его.
                    continue
                if effect == 'deny' and result:
                    return True
                elif effect == 'allow' and not result:
                    return False
            return False if effect == 'deny' else True

        return filter(condition_filter, matched)
