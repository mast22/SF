
AGENT_GROUP_NAME = 'agent_{id}'
ORDER_GROUP_NAME = 'order_{id}'


def get_agent_group_name(agent_id):
    return AGENT_GROUP_NAME.format(id=agent_id)


def get_order_group_name(order_id):
    return ORDER_GROUP_NAME.format(id=order_id)
