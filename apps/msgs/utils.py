import json
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse
from urllib import request
from typing import Mapping
from django.conf import settings

from apps.common.utils import import_from_string, import_from_module
from . import const as c
from . import logger
from .exceptions import ProviderError, ProviderBadResponseError


def select_task(receiver, msg_source, msg_type):
    """Выбор таска из потока Django"""
    provider_name, send_method = select_sending_provider(receiver, msg_source, msg_type)
    task_name = get_task_name(provider_name)
    task = import_from_module('apps.msgs.tasks', task_name)
    if task is None:
        raise KeyError(f'There is no task "{task_name}" for user: {receiver} msg_source: {msg_source},'
                       f' msg_type: {msg_type}. Provider name: {provider_name}, send_method: {send_method}')
    return task



def push_provider_selector(user, msg_settings, *args, **kwargs):
    """Метод для выбора push-провайдера. Простой случай - берём DUMMY, если DEBUG, иначе берём WEB"""
    device_type = getattr(user, 'push_device_type', 'WEB')
    provider_name = msg_settings.get('provider', {}).get(device_type, None)
    if not provider_name:
        raise KeyError(f'Wrong user.device_type: {device_type} or msg_settings: {msg_settings}')
    return provider_name


def load_method(method_path: str):
    return import_from_string(method_path)


def get_provider_class(provider_item):
    class_name = provider_item.get('provider', None)
    if class_name:
        provider_class = import_from_string(class_name)
    else:
        raise KeyError(f'There is no provider class in settings for {class_name}. Options were: {provider_item}')
    default_settings = provider_item.get('provider_settings', {})
    return provider_class, default_settings


# def get_task(receiver, msg_source, msg_type):
#     provider_name, send_method = select_sending_method(receiver, msg_source, msg_type)
#     task_name = get_task_name(provider_name)
#     task = import_from_module('apps.msgs.tasks', task_name)
#     if task is None:
#         raise KeyError(f'There is no task "{task_name}" for user: {receiver} msg_source: {msg_source},'
#                        f' msg_type: {msg_type}. Provider name: {provider_name}, send_method: {send_method}')
#     return task


def get_task_name(provider_name: str):
    return provider_name.strip().replace('.', '_') + '_task'


def select_sending_provider(receiver, msg_source, msg_type):
    """Выбирает конкретный метод для отправки сообщения"""
    message_settings = getattr(settings, 'MESSAGES_SETTINGS', {})
    send_method_conf = message_settings.get(msg_source, {}).get(msg_type, None)
    if send_method_conf is None:
        raise ValueError(f'There is not method for msg_source: {msg_source} and msg_type: {msg_type}')
    choose_provider_by = send_method_conf.get('choose_provider_by', None)
    if choose_provider_by:
        choose_provider_method = load_method(choose_provider_by)
        provider_name = choose_provider_method(receiver, send_method_conf)
    else:
        provider_name = send_method_conf['provider']

    send_method = send_method_conf.get('method', None)
    return provider_name, send_method


def select_sending_method(msg_source, msg_type):
    """Выбирает конкретного провайдера для отправки сообщения."""
    message_settings = getattr(settings, 'MESSAGES_SETTINGS', {})
    send_method_conf = message_settings.get(msg_source, {}).get(msg_type, None)
    if send_method_conf is None:
        raise ValueError(f'There is not method for msg_source: {msg_source} and msg_type: {msg_type}')
    send_method = send_method_conf.get('method', None)
    options = send_method_conf.get('options', {})
    return send_method, options



def make_request(url: str,
                 method='GET',
                 headers: Mapping=None,
                 params: Mapping=None,
                 data: Mapping or str=None,
                 req_type: str=None,
                 resp_type: str='JSON',
                 timeout: int=c.DEFAULT_REQUEST_TIMEOUT):
    """
    Отправляет запрос, возвращает ответ в виде JSON, XML или строки.
    :param url: URL для отправки запроса
    :param method: один из ('GET', 'POST', 'PUT', 'DELETE', 'HEAD')
    :param headers: дополнительные заголовки в запросе
    :param params: дополнительные GET-параметры (добавляются в строку URL)
    :param data: дополнительные POST-параметры
    :param req_type: None, 'JSON', "XML', 'URLENCODED' - добавляет доп. заголовки в request
           и правильно конвертит data
    :param resp_type: тип ответа. 'JSON' (по умолчанию), 'XML' или None для возврата ответа как есть
    :param timeout: таймаут ожидания ответа от сервера, если не задано, берём self.REQUEST_TIMEOUT
    """
    method = method.upper()
    if method not in ('GET', 'POST', 'PUT', 'DELETE', 'HEAD'):
        raise ValueError('_make_request method argument is wrong: {0}'.format(method))
    if params and isinstance(params, Mapping):
        url = add_url_params(url, params)
    headers = headers if headers else {}

    if data:
        if req_type == 'JSON':
            headers['content-type'] = 'application/json'
            try:
                data = json.dumps(data).encode()
            except Exception as err:
                raise ProviderError('_make_request has a problem with converting data to json: {0}'.format(err))
        elif req_type == 'XML':
            headers['content-type'] = 'application/xml'
            if type(data) == str:
                data = data.encode()
            elif isinstance(data, Mapping):
                data = convert_to_xml(data)
        elif req_type == 'URLENCODED':
            headers['content-type'] = 'application/x-www-form-urlencoded'
            data = urlencode(data).encode()

    logger.warning(f'make_request. Sent to {url} method={method}, headers: {headers} data: {data}')

    req = request.Request(url, method=method, headers=headers, data=data)
    with request.urlopen(req, timeout=timeout) as resp:
        resp_code = int(resp.getcode())
        resp_value = str(resp.read().decode())

    logger.warning(f'make_request. Response code: {resp_code} data: {resp_value}')

    if not (200 <= resp_code <= 299):
        raise ProviderBadResponseError('_make_request. provider answer: {0} {1}'.format(resp_code, resp_value))

    if resp_type == 'JSON':
        try:
            resp_value = json.loads(resp_value)
        except json.JSONDecodeError as err:
            raise ProviderError(f'_make_request has problems with json: {err} resp: {resp_code} {resp_value}')
    elif resp_type == 'XML':
        try:
            import xmltodict
            resp_value = xmltodict.parse(resp_value)
        except Exception as err:
            raise ProviderError(f'_make_request has problems with XML: {err} resp: {resp_code} {resp_value}')
    return resp_value



def add_url_params(url: str, params: Mapping):
    """Добавляет GET параметры к уже имеющимся в URL-адресе"""
    # NOTE: Взято со stackoverflow. Возможно, стоит вынести в utils, когда код будет закончен.
    url_parts = list(urlparse(url))
    query = dict(parse_qsl(url_parts[4]))
    query.update(params)
    url_parts[4] = urlencode(query)
    return urlunparse(url_parts)


def convert_to_xml(data: Mapping, root: str='data', pretty: bool=False) -> str:
    """
    Преобразует словарь аргументов kwargs в XML-представление, пригодное для smsint.ru

    :param data: Словарь, где ключ - имя xml-элемента: значение - значение xml-элемента
    :param root: Имя корневого элемента (по умолч.: data)
    :param pretty: Нужно ли красиво отформатировать сгенерированный xml
    :return str: сгенерированный xml-документ

    Пример:
    >>> convert_to_xml({'to':{'text':'Текст','phone':'+798712345'}, 'text': 'Пример'}, pretty=True)
    '''<?xml version="1.0" encoding="UTF-8"?>
    <data>
        <to phone="+798712345">Текст</to>
        <text>Пример</text>
    </data>'''
    """
    header_str = '<?xml version="1.0" encoding="UTF-8"?>'
    root_str = '\n<{0}>\n{1}</{0}>' if pretty else '<{0}>{1}</{0}>'
    line = '    <{0}{2}>{1}</{0}>\n' if pretty else '<{0}{2}>{1}</{0}>'
    xml_list = []
    for k, v in data.items():
        if isinstance(v, Mapping):
            options = ['{0}="{1}"'.format(o_name, o_val) for o_name, o_val in v.items() if o_name != 'text']
            options = ' ' + ' '.join(options)
            value = v.get('text', '')
        else:
            options = ''
            value = v
        xml_list.append(line.format(k, value, options))
    return header_str + root_str.format(root, ''.join(xml_list))



