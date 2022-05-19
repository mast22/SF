import dataclasses
from json.decoder import JSONDecodeError
from typing import Optional

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.orders.const import ORDER_STATUSES_ACTIVE
from apps.orders.models import Order
from apps.users.const import TokenType
from apps.users.models import Token
from . import logger
from .utils import get_agent_group_name

from .serializer_ws import serialize_error
from .const import WSMessageError


@dataclasses.dataclass
class AuthorizationResult:
    user: Optional["User"] = None
    error: Optional[str] = None


@database_sync_to_async
def _get_active_orders(agent_id):
    orders = Order.objects.filter(agent_id=agent_id, status__in=ORDER_STATUSES_ACTIVE)
    orders = orders.values_list('id', flat=True)
    return list(orders)


@database_sync_to_async
def ws_authorize(auth_token) -> AuthorizationResult:
    """Авторизация пользователя по auth-токену"""
    auth_token = auth_token.split(' ')

    if len(auth_token) != 2 or auth_token[0] != 'Token':
        result = AuthorizationResult(error=WSMessageError.WRONG_TOKEN_FORM)
    else:
        try:
            token = Token.objects.get_token(key=auth_token[1], token_type=TokenType.ACCESS, select_related=('user',))
            result = AuthorizationResult(user=token.user)
        except Token.TokenIsOutdatedException:
            result = AuthorizationResult(error=WSMessageError.TOKEN_IS_OUTDATED)

    return result


class AgentConsumer(AsyncJsonWebsocketConsumer):
    """Заготовка ws-сервера для работы со статусами заказа"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent = None
        self.channel_group = None

    async def connect(self):
        await self.accept()

    async def disconnect(self, code):
        if self.channel_group:
            # Если мы подключили группу, то выбрасываем её
            await self.channel_layer.group_discard(self.channel_group, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if self.agent is None:
            await self._receive_authentication(content, **kwargs)
        else:
            await self._receive_incoming_message(content, **kwargs)

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        """ Валидация запроса в json """
        try:
            await super(AgentConsumer, self).receive(text_data, bytes_data, **kwargs)
        except JSONDecodeError:
            await self.send_json(serialize_error(WSMessageError.CANT_DECODE))
            await self.close()

    async def _receive_authentication(self, content, **kwargs):
        """Авторизация юзера по токену."""
        if 'auth_token' not in content:
            logger.info(f'First message from agent without auth_token: {content}')
            await self.send_json(serialize_error(WSMessageError.BEARER_NOT_PROVIDED))
            await self.close()

            return

        auth_result = await ws_authorize(content['auth_token'])
        if auth_result.error is not None:
            await self.send_json({'error': auth_result.error})
            await self.close()

            return
        else:
            self.agent = auth_result.user

        self.channel_group = get_agent_group_name(self.agent.id)
        await self.channel_layer.group_add(self.channel_group, self.channel_name)
        await self.send_json({
            'detail': 'Authorization complete.',
            'user_id': self.agent.id,
        })

    async def _receive_incoming_message(self, content, **kwargs):
        """Любое другое входящее сообщение."""
        await self.send_json(serialize_error(WSMessageError.INCOMING_MESSAGES_ARE_NOT_ALLOWED))

    async def agent_notification(self, event):
        await self.send_json({
            'type': event['notification_type'],
            'order': event['order_id'],
            'data': event['data'],
        })
