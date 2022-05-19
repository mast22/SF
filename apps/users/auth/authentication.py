from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework import exceptions as exc
from django.utils.translation import gettext as _
from django.contrib.auth.backends import ModelBackend

from ..models.tokens import Token
from ..const import ACCESS_TOKEN_KEYWORD, TokenType


class ModelBackendWithCache(ModelBackend):
    """Placeholder for future usage"""
    pass


class TokenAuthentication(BaseAuthentication):
    """
    Simple token based authentication.

    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "Token ".  For example:

        Authorization: Token 401f7ac837da42b97f613d789819ff93537bee6a

    For now it's just a copy of drf.authentication.TokenAuthentication
    but this model will be changed a lot in future.
    """
    keyword = ACCESS_TOKEN_KEYWORD
    model = Token

    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None

        if len(auth) == 1:
            msg = _('Invalid token header. No credentials provided.')
            raise exc.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid token header. Token string should not contain spaces.')
            raise exc.AuthenticationFailed(msg)

        try:
            token = auth[1].decode()
        except UnicodeError:
            msg = _('Invalid token header. Token string should not contain invalid characters.')
            raise exc.AuthenticationFailed(msg)

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, key):
        try:
            token = self.model.objects.get_token(key=key, token_type=TokenType.ACCESS, select_related=['user'])
        except self.model.TokenIsOutdatedException:
            raise exc.AuthenticationFailed(_('Invalid token.'))

        if not token.user.is_active:
            raise exc.AuthenticationFailed(_('User inactive or deleted.'))

        return token.user, token

    def authenticate_header(self, request):
        return self.keyword


def token_logout(request):
    user = request.user
    if user.is_anonymous:
        raise exc.AuthenticationFailed(_('User is not logged in.'))
    Token.objects.filter(user=user, type__in=(TokenType.ACCESS, TokenType.REFRESH)).delete()
    request.user = None
    return user
