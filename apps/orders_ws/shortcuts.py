# Shortcuts for rest
from typing import Type
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from . import logger
from .utils import get_agent_group_name
from .const import WSMessageType


def send_message_sync(
            agent_id: Type[int],
            order_id: Type[int],
            type: Type[str] = None,
            data=None,
            action: str = 'notification'
    ):
    return async_to_sync(send_message_async)(
        agent_id,
        order_id,
        type,
        data,
        action,
    )


async def send_message_async(agent_id: int, order_id: int, type: str = None, data=None, action: str = 'notification'):
    if type not in WSMessageType.keys():
        raise ValueError(f'Wrong type: {type}, order_id: {order_id}, data: {data}')
    group_name = get_agent_group_name(agent_id)
    chl = get_channel_layer()
    logger.debug(f'Send notification to agent {agent_id} for order: {order_id}'
                 f' of type: {type} to a channel group: {group_name} data: {data}')
    print(f'send_message_async. agent_id={agent_id}, order_id={order_id}, notification_type={type}, data={data}')
    await chl.group_send(
        group_name,
        {
            'type': 'agent.notification',
            'notification_type': type,
            'order_id': order_id,
            'data': data,
        }
    )
