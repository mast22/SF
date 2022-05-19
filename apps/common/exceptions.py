from rest_framework.exceptions import APIException, status
from django.utils.translation import gettext_lazy as __


class BadStateException(APIException):
    """ Универсальное исключение для отображения проблемы на интерфейс пользователя

    Давайте не будем усложнять систему разношерстными исключениями если большинство случаев
    можно обойти используя исключением валидации и эти "плохим состоянием"
    """
    status_code = status.HTTP_409_CONFLICT
    default_detail = __('Bad State (409)')
    default_code = 'bad_state'
