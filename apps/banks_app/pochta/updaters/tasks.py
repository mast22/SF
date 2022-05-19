import dramatiq

from apps.orders.models import OrderCreditProduct
from ..provider import PochtaBankProvider



@dramatiq.actor
def check_order_status(ocp_id: int):
    """ Вызываем сервер BrokerOpportunityStatus для получение статуса  """
    ocp = OrderCreditProduct.objects.get(ocp_id)
    provider = PochtaBankProvider(ocp=ocp)
    provider.check_scoring_result()

