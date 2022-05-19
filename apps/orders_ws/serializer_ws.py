""" Аналоги сериалайзеров DRF для ws. Чтобы не добавлять новую зависимость для форматирования  """
from .const import WSMessageError


def serialize_error(code: str):
    """
    'error': {
        'code': '<code>',
        'detail': 'detail'
    }
    """

    return {
        'type': 'error',
        'code': code,
        'detail': WSMessageError.plural(code)
    }
