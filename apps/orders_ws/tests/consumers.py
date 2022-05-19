import asyncio
# from django.test.utils import override_settings
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from channels.layers import channel_layers

from apps.orders_ws.consumers import AgentConsumer
from apps.orders_ws import const as c
from apps.orders_ws.shortcuts import send_message_async

# WAIT_TIMEOUT = 10
WAIT_TIMEOUT = 30000 # For debug


@database_sync_to_async
def get_order_and_ocp_for_agent(user):
    from apps.orders.models import Order
    order = Order.objects.filter(agent_id=user.id) \
        .select_related('outlet', 'credit', 'family_data',
                        'personal_data', 'passport', 'career_education',
                        'extra_data', 'client_order', 'telegram_order') \
        .prefetch_related('goods', 'credit_products', 'order_credit_products') \
        .order_by('id').first()
    ocp = order.order_credit_products.all()[0]
    return order, ocp


@database_sync_to_async
def get_auth_agent(agent=None):
    from apps.users.models import Agent, Token
    if not agent:
        agent = Agent.objects.first()
    refresh, access = Token.objects.create_auth_tokens(agent)
    return agent, refresh, access


async def initiate_connection(url, user=None):
    """Initiate a connection to a websocket server and send a handshake then sleep 0.1 second to be sure all works well."""
    communicator = WebsocketCommunicator(AgentConsumer.as_asgi(), url)
    connected, subprotocol = await communicator.connect(timeout=WAIT_TIMEOUT)
    assert connected
    user, refresh_token, access_token = await get_auth_agent(agent=user)
    handshake = {
        'auth_token': f'Token {access_token.key}',
    }
    await communicator.send_json_to(data=handshake)
    h_resp = await communicator.receive_json_from(timeout=WAIT_TIMEOUT)
    assert 'detail' in h_resp, f'Wrong response: {h_resp}'
    assert h_resp['user_id'] == user.id, f'Wrong response: {h_resp}'
    await asyncio.sleep(0.1)
    return communicator, user


import pytest


@pytest.fixture
def users_fixture():
    from apps.testing.fixtures.all_data import create_fixtures
    create_fixtures(levels=['banks'])
    from apps.users.models import Agent
    agent = Agent.objects.first()
    return agent


@pytest.fixture
def agent_order_fixture():
    from apps.testing.fixtures.all_data import create_fixtures
    create_fixtures(levels=['banks', 'full_order'])
    from apps.users.models import Agent
    agent = Agent.objects.first()
    return agent


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_handshake(users_fixture):
    """Test of hanshake initiation. Nothing else"""
    agent = users_fixture
    communicator, user = await initiate_connection(url='order-updates/')
    assert agent.id == user.id, f'При аутентификации получен неправильный пользователь'
    await communicator.disconnect()
    channel_layers.backends.clear()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_get_scoring_finished_notification(agent_order_fixture):
    """Test of receiving notification about scoring finished for one credit product"""
    user = agent_order_fixture
    communicator, user = await initiate_connection(url='order-updates/', user=user)
    order, ocp = await get_order_and_ocp_for_agent(user)
    data = dict(
        order_credit_product=ocp.id,
        credit_product=ocp.credit_product_id,
        scoring_status=ocp.status
    )
    await send_message_async(agent_id=user.id, order_id=order.id, type=c.WSMessageType.SCORING_RESULT, data=data)
    resp = await communicator.receive_json_from(timeout=WAIT_TIMEOUT)

    assert resp['type'] == c.WSMessageType.SCORING_RESULT, f'Wrong resp: {resp}'
    assert resp['order'] == order.id, f'Wrong resp: {resp}'
    assert resp['data']['order_credit_product'] == ocp.id, f'Wrong resp: {resp}'
    assert resp['data']['credit_product'] == ocp.credit_product_id, f'Wrong resp: {resp}'
    assert resp['data']['scoring_status'] == ocp.status, f'Wrong resp: {resp}'

    assert await communicator.receive_nothing() is True, 'Пришли данные после последнего сообщения'
    await communicator.disconnect()
    channel_layers.backends.clear()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_send_wrong_token():
    """Initiate a connection to a websocket server and send a handshake then sleep 0.1 second to be sure all works well."""
    url = '/order-updates/'
    communicator = WebsocketCommunicator(AgentConsumer.as_asgi(), url)
    connected, subprotocol = await communicator.connect(timeout=WAIT_TIMEOUT)
    assert connected
    handshake = {
        'auth_token': f'Bearer some_wrong_token',
    }
    await communicator.send_json_to(data=handshake)
    h_resp = await communicator.receive_json_from(timeout=WAIT_TIMEOUT)

    assert 'error' in h_resp, f'Неправильный ответ: {h_resp}'
