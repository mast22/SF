from typing import Optional

from apps.orders.models import OrderCreditProduct
from .... import logger


def get_ocp(bank_id: int) -> Optional[OrderCreditProduct]:
    try:
        return OrderCreditProduct.objects.select_related(
            'order', 'credit_product', 'credit_product__bank', 'order__contract',
        ).get(bank_id=bank_id)
    except OrderCreditProduct.DoesNotExist:
        logger.error(f'OCP для bank_id %s не найден. Вероятно ошибка в сохранении данных', bank_id )
        return None
