import requests
import dramatiq
from .models import Delivery, CdekToken
from . import const as c


def make_request_order_by_cdek_number(cdek_number: str) -> requests.Response:
    """ Запрос информации по uuid заказа """
    token = CdekToken.get_value()
    response = requests.get(
        f'{c.SDEK_API_URI}orders?cdek_number={cdek_number}',
        headers={'Authorization': f'Bearer {token}'},
        timeout=5
    )
    return response


def validate_and_create_delivery(cdek_uuid: str):
    """ Создаём новую доставку Делаем запрос в СДЭК чтобы проверить код накладной """
    response = make_request_order_by_cdek_number(cdek_uuid)
    delivery, _ = Delivery.objects.create(

    )
    if response.status_code == 200:
        delivery.is_valid = True
        delivery.save()
    else:
        delivery.is_valid = False
    return


@dramatiq.actor
def update_deliveries():
    """ Проверяем статусы всех недоставленных заказов
    Запускается периодической задачей из APScheduler

    Странно, что cdek не додумался сделать список доставок,
    придется делать запрос на каждую доставку отдельно
    """
    for delivery in Delivery.objects.all():
        response = make_request_order_by_cdek_number(delivery.cdek_number)
        if response.status_code == 200:
            data = response.json()
            recent_status = data['statuses'][-1:]['code']
            delivery.cdek_status = recent_status
            delivery.save()
        else:
            # TODO
            raise Exception('Ошибка запроса к СДЭК')
