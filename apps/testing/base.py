from typing import Tuple, Dict, List, Callable, Sequence, Set
from io import BytesIO
from unittest import TestCase, mock
from rest_framework.test import APITestCase, APITransactionTestCase, APIClient
from django.test.testcases import TestCase as dj_TestCase
from rest_framework import status as st
from django.db import models as m
from django.core.cache import caches
from django.core.management import call_command
from django.conf import settings

from apps.common.utils import is_iterable
from apps.common.utils import model_to_dict
from apps.users.models import User


def clear_all_caches():
    used_caches = caches.all()
    for cache in used_caches:
        cache.clear()


def load_fixtures(cls, fixture_settings=None):
    if not fixture_settings:
        fixture_settings = {}
    for method in cls.model_fixtures:
        result = method(**fixture_settings)
        if result:
            for key, created_objects in result.items():
                if not created_objects:
                    created_objects = {}
                dict_of_objects = getattr(cls, key, None)
                if dict_of_objects and isinstance(dict_of_objects, dict):
                    dict_of_objects.update(created_objects)
                else:
                    dict_of_objects = created_objects
                setattr(cls, key, dict_of_objects)


class BaseMockedUrloppenTest(TestCase):
    RESPONSE_HEADERS_DEFAULT = {}

    def setUp(self):
        self.mock_get_patcher = mock.patch('urllib.request.urlopen')
        self.mock_urlopen = self.mock_get_patcher.start()

    def tearDown(self):
        self.mock_get_patcher.stop()
        self.mock_urlopen = None
        clear_all_caches()

    def _mock_return_value(self, body=None, code=200, headers=None):
        self.mock_urlopen.return_value = BytesIO(body)
        self.mock_urlopen.return_value.getcode = lambda: code
        headers = headers if headers else {}
        headers_in_response = {**self.RESPONSE_HEADERS_DEFAULT, **headers}
        self.mock_urlopen.info = lambda: headers_in_response


class CRUDTestCase(APITestCase):
    """ Проверка доступнности CRUD запросов на модель """

    client = APIClient()

    test_case_data = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.__class__ == CRUDTestCase:
            # Rebind `run' from the parent class.
            self.run = lambda self, *args, **kwargs: None

    def setUp(self) -> None:
        from apps.users.models import User
        self.user = User.objects.create_superuser(phone_number='9880002233', password='admin1234vcvfds')

    def tearDown(self):
        clear_all_caches()

    def make_request(self, method_type, url, data=None):
        methods = {
            'list': 'get',
            'retrieve': 'get',
            'create': 'post',
            'partial_update': 'patch',
            'update': 'put',
        }
        self.client.force_login(user=self.user)
        return getattr(self.client, methods[method_type])(url, data, format='json')

    def test_run_tests(self):
        assert self.test_case_data, 'Задайте аттрибут test_case_data'
        for test_case in self.test_case_data:
            response = self.make_request(test_case['method_type'], test_case['url'], test_case['data'])
            self.assertEqual(response.status_code, test_case['status_code'], test_case['comment'])


class BaseTransactionViewSetTestCase(APITransactionTestCase):
    # Набор callable, возвращающий словарь в формате:
    # {'model_key': {dict: 'of', 'created': instances}
    # Все фикстуры будут созданы в методе setUpTestData
    # И присвоены классу по model_key
    model_fixtures = []

    def __init__(self, *args, **kwargs):
        super(BaseTransactionViewSetTestCase, self).__init__(*args, **kwargs)
        if self.__class__ == BaseViewSetTestCase:
            # Rebind `run' from the parent class.
            self.run = lambda self, *args, **kwargs: None

    @classmethod
    def setUpClass(cls, fixture_settings=None):
        # from apps.testing.fixtures.organizations import clear_all
        # clear_all()
        super().setUpClass()
        load_fixtures(cls, fixture_settings)

    def tearDown(self):
        super().tearDown()
        clear_all_caches()
        # from apps.testing.fixtures.organizations import clear_all
        # clear_all()


class BaseViewSetTestCase(APITestCase):
    # Набор callable, возвращающий словарь в формате:
    # {'model_key': {dict: 'of', 'created': instances}
    # Все фикстуры будут созданы в методе setUpTestData
    # И присвоены классу по model_key
    model_fixtures = []
    serializer = None

    # Набор url для стандартных методов
    url_create_instance = '/api/{model}/'
    url_view_list = '/api/{model}/'
    url_view_instance = '/api/{model}/{id}/'
    url_update_instance = '/api/{model}/{id}/'
    url_delete_instance = '/api/{model}/{id}/'

    # Словарь пользователей, нужно заполнить в фикстурах
    # Тут указаны только примеры того, что нужно вернуть, все данные должны вернуться
    # из фикстур в формате {'objects': {'name': object, 'name2': object2}, 'another_model': {...}}
    users = {}
    cities = {}
    orgs = {}
    objects = {}

    def __init__(self, *args, **kwargs):
        super(BaseViewSetTestCase, self).__init__(*args, **kwargs)
        if self.__class__ == BaseViewSetTestCase:
            # Rebind `run' from the parent class.
            self.run = lambda self, *args, **kwargs: None

    @classmethod
    def setUpClass(cls):
        super(dj_TestCase, cls).setUpClass()
        if not cls._databases_support_transactions():
            return
        cls.cls_atomics = cls._enter_atomics()

        if cls.fixtures:
            for db_name in cls._databases_names(include_mirrors=False):
                try:
                    call_command('loaddata', *cls.fixtures, **{'verbosity': 0, 'database': db_name})
                except Exception:
                    cls._rollback_atomics(cls.cls_atomics)
                    cls._remove_databases_failures()
                    raise
        try:
            cls.setUpTestData()
        except Exception:
            cls._rollback_atomics(cls.cls_atomics)
            cls._remove_databases_failures()
            raise

    @classmethod
    def setUpTestData(cls, fixture_settings=None):
        load_fixtures(cls, fixture_settings)

    def tearDown(self):
        super().tearDown()
        clear_all_caches()

    @classmethod
    def get_users(cls, user_keys, *args):
        """Получает список пользователей"""
        if args:
            user_keys = (user_keys,) + tuple(args)
        elif isinstance(user_keys, str):
            user_keys = (user_keys,)
        return [cls.users[key] for key in user_keys]

    @staticmethod
    def get_url_with_params(url, params):
        if not params:
            return url
        p_to_join = []
        for k, v in params.items():
            if is_iterable(v):
                v = ','.join(v)
            p_to_join.append('{0}={1}'.format(k, v))
        return url + '?' + '&'.join(p_to_join)

    def make_request(
        self, url: str, user: User or None = None,
        data: dict or None = None, method: str = 'post',
        format: str = 'json', headers: dict = None
    ):
        if headers is None:
            headers = {}
        if data is None:
            data = {}
        if user is None:
            user = {}
        if user:
            self.client.force_login(user=user)
        rest_method = getattr(self.client, method.lower())
        response = rest_method(path=url, data=data, format=format, **headers)
        if user:
            self.client.logout()
        return response

    def create_instance(self, model_name, current_user, instance):
        json_data = self.serializer_instance(instance)
        url = self.url_create_instance.format(model=model_name)
        response = self.make_request(url, user=current_user, data=json_data, method='post')
        return response

    def view_list(self, model_name, current_user=None, params=None):
        url = self.url_view_list.format(model=model_name)
        url = self.get_url_with_params(url, params)
        response = self.make_request(url, user=current_user, method='get')
        return response

    def view_instance(self, model_name, current_user=None, instance_id=None, params=None):
        url = self.url_view_instance.format(model=model_name, id=instance_id)
        url = self.get_url_with_params(url, params)
        response = self.make_request(url, user=current_user, method='get')
        return response

    def update_instance(self, model_name, current_user, instance_id, instance):
        json_data = self.serializer_instance(instance)
        url = self.url_update_instance.format(model=model_name, id=instance_id)
        response = self.make_request(url, user=current_user, data=json_data, method='put')
        return response

    def partial_update_instance(self, model_name, current_user, instance_id, fields):
        url = self.url_update_instance.format(model=model_name, id=instance_id)
        response = self.make_request(url, user=current_user, data=fields, method='patch')
        return response

    def delete_instance(self, model_name, current_user, instance_id):
        url = self.url_delete_instance.format(model=model_name, id=instance_id)
        response = self.make_request(url, user=current_user, method='delete')
        return response

    def request_instance_action(
            self,
            model_name: str,
            current_user,
            instance_id: int or None,
            action: str,
            payload: dict,
            method: str = 'post',
    ):
        if instance_id is None:
            url = f'/api/v1/{model_name}/{action}/'
        else:
            url = f'/api/v1/{model_name}/{instance_id}/{action}/'
        resp = self.make_request(url, current_user, data=payload, method=method)
        return resp

    @classmethod
    def get_default_fields(cls, current_user):
        """
        Метод необходимо переопределить в дочернем классе для конкретной модели.
        Должен возвращать словарь из полей по умолчанию, необходимых для создания/изменения объекта.
        """
        return {}

    @classmethod
    def _get_fields_with_defaults(cls, fields=None, current_user=None):
        fields_default = cls.get_default_fields(current_user)
        return {**fields_default, **fields} if fields else fields_default

    @classmethod
    def serializer_instance(cls, obj, custom_serializer=None):
        serializer = custom_serializer or cls.serializer
        result = serializer(obj).data
        del result['id']  # Нам не нужен Ид для создания

        return result

    @staticmethod
    def get_content(resp):
        try:
            content = resp.json()
        except Exception:
            content = resp.content
        return content


class BasePermissionsTestCase(BaseViewSetTestCase):
    """
    Тесты, проверяющие права доступа пользователя к типовым методам api.

    users_allowed_*, users_forbidden_* задаются в формате:
    { user_instance: [model_instance, ...], ... },
    где model_instance либо непосредственно объект Model,
    либо callable, возвращающий объект Model.

    Для тестов users_*_create вместо Model используется словарь key:value
    в fields_to_check- список полей, которые необходимо проверить после создания/изменения записей.

    Для кастомных методов используется формат:
    { custom_action_name: { user_instance: [iterable_of_model_instances], ... }, }

    """
    model = None
    model_name = None
    pk_field = 'id'
    statuses_forbidden = [st.HTTP_403_FORBIDDEN]

    # List of fields to check after create/update
    fields_to_check = []
    fields_to_check_create = None

    # Dict of custom field checking logic. key: field name, value: function that check correctness
    fields_custom_logic = {}

    users_allowed_view = {}
    users_forbidden_view = {}

    users_allowed_create = {}
    users_forbidden_create = {}

    users_allowed_update = {}
    users_forbidden_update = {}

    users_allowed_delete = {}
    users_forbidden_delete = {}

    users_allowed_detail_actions = {}
    users_forbidden_detail_actions = {}
    instance_id = None

    users_allowed_list_actions = {}
    users_forbidden_list_actions = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.__class__ == BasePermissionsTestCase:
            self.run = lambda self, *args, **kwargs: None
        else:
            self.model_name = self.model.JSONAPIMeta.resource_name

    @classmethod
    def setUpTestData(cls, **kwargs):
        super().setUpTestData()
        cls.users_allowed_view, cls.users_forbidden_view = cls.setup_view_data()
        cls.users_allowed_create, cls.users_forbidden_create = cls.setup_create_data()
        cls.users_allowed_update, cls.users_forbidden_update = cls.setup_update_data()
        cls.users_allowed_delete, cls.users_forbidden_delete = cls.setup_delete_data()
        cls.users_allowed_detail_actions, cls.users_forbidden_detail_actions, cls.instance_id = cls.setup_detail_actions_data()
        cls.users_allowed_list_actions, cls.users_forbidden_list_actions = cls.setup_list_actions_data()

    @classmethod
    def setup_view_data(cls) -> Tuple[Dict[m.Model, List], Dict]:
        return {}, {}

    @classmethod
    def setup_create_data(cls):
        return {}, {}

    @classmethod
    def setup_update_data(cls):
        return {}, {}

    @classmethod
    def setup_delete_data(cls):
        return {}, {}

    @classmethod
    def setup_detail_actions_data(cls) -> Tuple[Dict[m.Model, List], Dict, int or None]:
        # Помимо запрещенных и разрешенных правил необходимо добавить
        # id объекта, который будет проверяться
        return {}, {}, None

    @classmethod
    def setup_list_actions_data(cls) -> Tuple[Dict[m.Model, List], Dict]:
        return {}, {}

    @staticmethod
    def _get_instances(objects_or_callables, current_user=None):
        """Сбор конечных инстансов моделей для тестов.
        Можно передать 1 или несколько объектов или словарей с полями модели,
        можно передать QuerySet, который вернёт список объектов
        можно передать callable, который вернёт объект, QuerySet или список объектов.
        Также можно сразу передавать iterable из всего перечисленного.
        Значения None и пустые результаты вызовов функции будут пропущены.

        Возвращает плоский список необходимых объектов.
        """

        def _get_recursive(objects_or_callable, cur_user):
            instances = []
            if not objects_or_callable:
                pass
            elif isinstance(objects_or_callable, m.Model) or isinstance(objects_or_callable, dict):
                instances.append(objects_or_callable)
            elif callable(objects_or_callable):
                result = objects_or_callable(cur_user)
                instances += _get_recursive(result, cur_user)
            else:
                try:
                    iterator = iter(objects_or_callable)
                except TypeError:
                    instances.append(objects_or_callable)
                else:
                    for object_or_callable in iterator:
                        instances += _get_recursive(object_or_callable, cur_user)
            return instances

        return _get_recursive(objects_or_callables, current_user)

    def instance_ids(self, instances) -> Set[str]:
        return {str(getattr(instance, self.pk_field)) for instance in instances}

    def fail_unless_response_has_data(self, response, user):
        """ Проверка на то, что в ответе пришёл именно ответ с данными, а не ошибка """
        json_data = response.json()
        if 'data' not in json_data:
            self.fail(f'User {user}, {self.model_name} ({self.pk_field}). Wrong result: {json_data}')

    def get_response_data(self, response) -> Dict:
        return response.json()['data']

    def get_result_ids(self, data: dict) -> Set[str]:
        return {str(result[self.pk_field]) for result in data}

    def get_response_instance_pk(self, response) -> str:
        return response.json()['data']['id']

    def test_view_is_allowed(self):
        for user, objects_or_callables in self.users_allowed_view.items():
            instances = self._get_instances(objects_or_callables, user)
            resp = self.view_list(self.model_name, user)
            self.assertEqual(resp.status_code, st.HTTP_200_OK,
                             msg=f'User {user} ({user.id}) need to be allowed to list {self.model_name}. Resp: {resp.json()}')
            if self.pk_field:
                instance_ids = self.instance_ids(instances)
                self.fail_unless_response_has_data(resp, user)
                data = self.get_response_data(resp)
                result_ids = self.get_result_ids(data)
                ids_not_in_result = instance_ids - result_ids
                instances_not_in_result = [instance for instance in instances if
                                           getattr(instance, self.pk_field) in ids_not_in_result]
                self.assertEqual(len(ids_not_in_result), 0,
                                 msg='User {0} ({1}) need to be allowed to see row with ids: {2} ({3}) in list of {4}. Resp: {5}'.format(
                                     user, user.id, str(ids_not_in_result), str(instances_not_in_result),
                                     self.model_name, resp.json()))

            for instance in instances:
                resp = self.view_instance(self.model_name, user, instance.id)
                self.assertEqual(resp.status_code, st.HTTP_200_OK,
                                 msg='User {0} ({1}) need to be allowed to retrieve {2} of {3}. Resp: {4}'.format(
                                     user, user.id, instance, self.model_name, resp.json()))
                if self.pk_field:
                    instance_id = str(getattr(instance, self.pk_field))
                    result_id = self.get_response_instance_pk(resp)
                    self.assertEqual(instance_id, result_id,
                                     msg='User {0} ({1}) got instance with wrong pk: {2}, need: {3}. Resp: {4}'.format(
                                         user, user.id, result_id, instance_id, resp.json()))

    def test_view_is_forbidden(self):
        for user, objects_or_callables in self.users_forbidden_view.items():
            instances = self._get_instances(objects_or_callables, user)

            resp = self.view_list(self.model_name, user)
            if 200 <= resp.status_code < 299:
                if self.pk_field:
                    instance_ids = self.instance_ids(instances)
                    self.fail_unless_response_has_data(resp, user)
                    data = self.get_response_data(resp)
                    result_ids = self.get_result_ids(data)
                    instance_ids_in_result = set.intersection(instance_ids, result_ids)
                    self.assertEqual(len(instance_ids_in_result), 0,
                                     msg='User {0} ({1}) need to be forbidden to see {2} in list of {3}. Resp: {4}'.format(
                                         user, user.id, str(instance_ids_in_result), self.model_name, resp.json()))

            for instance in instances:
                resp = self.view_instance(self.model_name, user, instance.id)
                self.assertIn(resp.status_code, (st.HTTP_403_FORBIDDEN, st.HTTP_404_NOT_FOUND),
                              msg='User {0} ({1}) need to be forbidden to retrieve {2} of {3}. Resp: {4}'.format(
                                  user, user.id, instance, self.model_name, resp.json()))

    def test_create_is_allowed(self):
        fields_to_check = self.fields_to_check_create \
            if self.fields_to_check_create is not None \
            else self.fields_to_check
        for user, objects_or_callables in self.users_allowed_create.items():
            instances = self._get_instances(objects_or_callables, user)

            for instance in instances:
                resp = self.create_instance(self.model_name, user, instance)
                self.assertEqual(
                    resp.status_code,
                    st.HTTP_201_CREATED,
                    msg='User {0} need to be allowed to add instance of {1} with fields {2}. Resp: {3}'.format(
                        user, self.model_name, instance, resp.json()
                    )
                )
                if fields_to_check:
                    data = resp.json()
                    for field in fields_to_check:
                        self.assertEqual(instance[field], data[field],
                                         msg='User {0}, instance of {1}. Field "{2}" is wrong: sent "{3}" got "{4}". Resp: {5}'.format(
                                             user, self.model_name, field, instance[field], data[field], resp.json()))
                if self.fields_custom_logic:
                    data = resp.json()
                    for field, callable in self.fields_custom_logic.items():
                        result, error = callable(instance[field], data[field], user=user, sent_data=instance,
                                                 resp_data=data)
                        self.assertTrue(result, msg=error)

    def test_create_is_forbidden(self):
        for user, objects_or_callables in self.users_forbidden_create.items():
            instances = self._get_instances(objects_or_callables, user)
            for instance in instances:
                resp = self.create_instance(self.model_name, user, instance)
                self.assertIn(resp.status_code, self.statuses_forbidden,
                              msg='User {0} need to be forbidden to add instance of {1} with fields: {2}. Resp: {3}'.format(
                                  user, self.model_name, instance, resp.json()))

    def test_update_is_allowed(self):
        for user, objects_or_callables in self.users_allowed_update.items():
            instances = self._get_instances(objects_or_callables, user)
            for instance in instances:
                resp = self.update_instance(self.model_name, user, instance[self.pk_field], instance)
                self.assertEqual(resp.status_code, st.HTTP_200_OK,
                                 msg='User {0} need to be allowed to update instance of {1} with fields: {2}. Resp: {3}'.format(
                                     user, self.model_name, instance, resp.json()))
                if self.fields_to_check:
                    data = resp.json()
                    for field in self.fields_to_check:
                        self.assertEqual(instance[field], data[field],
                                         msg='User {0}, instance of {1}. Field "{2}" is wrong: sent "{3}" got "{4}". Resp: {5}'.format(
                                             user, self.model_name, field, instance[field], data[field], resp.json()))
                if self.fields_custom_logic:
                    data = resp.json()
                    for field, callable in self.fields_custom_logic.items():
                        result, error = callable(instance[field], data[field], user=user, sent_data=instance,
                                                 resp_data=data)
                        self.assertTrue(result, msg=error)

    def test_update_is_forbidden(self):
        for user, objects_or_callables in self.users_forbidden_update.items():
            instances = self._get_instances(objects_or_callables, user)
            for instance in instances:
                resp = self.update_instance(self.model_name, user, getattr(instance, self.pk_field), instance)

                self.assertIn(resp.status_code, [st.HTTP_403_FORBIDDEN, st.HTTP_404_NOT_FOUND],
                              msg='User {0} need to be forbidden to update instance of {1} with fields: {2}. Resp: {3}'.format(
                                  user, self.model_name, instance, resp.json()))

    def test_delete_is_allowed(self):
        for user, objects_or_callables in self.users_allowed_delete.items():
            instances = self._get_instances(objects_or_callables, user)
            for instance in instances:
                resp = self.delete_instance(self.model_name, user, getattr(instance, self.pk_field))
                instance.save()  # Восстанавливаем обратно

                self.assertEqual(resp.status_code, st.HTTP_204_NO_CONTENT,
                                 msg='User {0} need to be allowed to delete instance of {1}: {2}. Resp: {3}'.format(
                                     user, self.model_name, instance, resp.data))

    def test_delete_is_forbidden(self):
        for user, objects_or_callables in self.users_forbidden_delete.items():
            instances = self._get_instances(objects_or_callables, user)
            for instance in instances:
                resp = self.delete_instance(self.model_name, user, getattr(instance, self.pk_field))
                instance.save()  # Восстанавливаем обратно

                self.assertIn(resp.status_code, [st.HTTP_403_FORBIDDEN, st.HTTP_404_NOT_FOUND],
                              msg='User {0} need to be forbidden to delete instance of {1} with fields: {2}. Resp: {3}'.format(
                                  user, self.model_name, instance, resp.data))

    # def run_tests_on_action(self, users_detail_actions: dict, message: str, statement: Callable, instance_id: int or None):
    #     def make_request(method='post'):
    #         return self.request_instance_action(self.model_name, user, instance_id, action, {}, method)
    #
    #     faulty_responses = []
    #     for user, actions in users_detail_actions.items():
    #         for action in actions:
    #             resp = None
    #             try:
    #                 # Получение ошибки - положительный результат, поскольку прошла проверка доступа и доступ
    #                 # был предоставлен
    #                 resp = make_request()
    #                 if resp.status_code == 405:
    #                     resp = make_request(method='get')
    #             except Exception as err:
    #                 print(user, action, 'Error:', err)
    #                 continue
    #
    #             try:
    #                 data = resp.json()
    #             except Exception as err:
    #                 data = str(resp.data)
    #
    #             if statement(resp):
    #                 # Сохраним методы которые упали с Permission Denied и отобразим их
    #                 faulty_responses.append(message.format(
    #                     action=action,
    #                     instance=instance_id,
    #                     user=user,
    #                     status_code=resp.status_code,
    #                     data=data,
    #                 ))
    #     faulty_responses = '\n'.join(faulty_responses)
    #
    #     self.failIf(bool(faulty_responses), str(faulty_responses))

    # def test_detail_action_is_allowed(self):
    #     is_faulty_statement = lambda response: response and response.status_code in (403, 404)
    #     message = 'Detail Action {action} must be allowed for {user} on object: {instance}.' \
    #         + ' Response: (status: {status_code}) {data}'
    #     users_detail_actions = self.users_allowed_detail_actions
    #     self.run_tests_on_action(users_detail_actions, message, is_faulty_statement, self.instance_id)
    #
    # def test_detail_action_is_forbidden(self):
    #     is_faulty_statement = lambda response: response and response.status_code not in (403, 404)
    #     message = 'Detail Action {action} must be restricted for {user} on object: {instance}.'\
    #         + ' Response: (status: {status_code}) {data}'
    #     users_detail_actions = self.users_forbidden_detail_actions
    #     self.run_tests_on_action(users_detail_actions, message, is_faulty_statement, self.instance_id)
    #
    # def test_list_action_is_allowed(self):
    #     is_faulty_statement = lambda response: response and response.status_code in (403, 404)
    #     message = 'List Action {action} must be allowed for {user} on object: {instance}.' \
    #         + ' Response: (status: {status_code}) {data}'
    #     users_detail_actions = self.users_allowed_list_actions
    #     self.run_tests_on_action(users_detail_actions, message, is_faulty_statement, None)
    #
    # def test_list_action_is_forbidden(self):
    #     is_faulty_statement = lambda response: response and response.status_code not in (403, 404)
    #     message = 'List Action {action} must be restricted for {user} on object: {instance}.' \
    #                 + ' Response: (status: {status_code}) {data}'
    #     users_detail_actions = self.users_forbidden_list_actions
    #     self.run_tests_on_action(users_detail_actions, message, is_faulty_statement, None)
