from apps.common.choices import Choices
from django.utils.translation import gettext_lazy as __


SDEK_API_URI = 'https://api.edu.cdek.ru/v2/'


class ContractLocation(Choices):
    IN_OUTLET = 'in_outlet', ('На точке')
    IN_OFFICE = 'in_office', ('В офисе')
    IN_POST = 'in_post', ('На почте')
    IN_BANK = 'in_bank', ('В банке')


class ContractCdekStatus(Choices):
    # На точке или в офисе
    ACCEPTED = 'ACCEPTED', __('Принят')
    CREATED = 'CREATED', __('Создан')
    # На почте
    ACCEPTED_AT_PICK_UP_POINT = 'ACCEPTED_AT_PICK_UP_POINT', __('Принят на склад до востребования')
    ACCEPTED_AT_RECIPIENT_CITY_WAREHOUSE = 'ACCEPTED_AT_RECIPIENT_CITY_WAREHOUSE', __('Принят на склад доставки')
    ACCEPTED_AT_TRANSIT_WAREHOUSE = 'ACCEPTED_AT_TRANSIT_WAREHOUSE', __('Принят на склад транзита')
    ACCEPTED_IN_TRANSIT_CITY = 'ACCEPTED_IN_TRANSIT_CITY', __('Встречен в г. транзите')
    ARRIVED_AT_RECIPIENT_CITY = 'ARRIVED_AT_RECIPIENT_CITY', __('Встречен в г. получателе')
    READY_FOR_SHIPMENT_IN_SENDER_CITY = 'READY_FOR_SHIPMENT_IN_SENDER_CITY', __('Не вручен')
    READY_FOR_SHIPMENT_IN_TRANSIT_CITY = 'READY_FOR_SHIPMENT_IN_TRANSIT_CITY', __('Выдан на отправку в г. отправителе')
    RECEIVED_AT_SENDER_WAREHOUSE = 'RECEIVED_AT_SENDER_WAREHOUSE', __('Выдан на отправку в г. транзите')
    RETURNED_TO_RECIPIENT_CITY_WAREHOUSE = 'RETURNED_TO_RECIPIENT_CITY_WAREHOUSE', __('Принят на склад отправителя')
    RETURNED_TO_SENDER_CITY_WAREHOUSE = 'RETURNED_TO_SENDER_CITY_WAREHOUSE', __('Возвращен на склад доставки')
    RETURNED_TO_TRANSIT_WAREHOUSE = 'RETURNED_TO_TRANSIT_WAREHOUSE', __('Возвращен на склад отправителя')
    SENT_TO_RECIPIENT_CITY = 'SENT_TO_RECIPIENT_CITY', __('Возвращен на склад транзита')
    SENT_TO_TRANSIT_CITY = 'SENT_TO_TRANSIT_CITY', __('Отправлен в г. получатель')
    TAKEN_BY_COURIER = 'TAKEN_BY_COURIER', __('Отправлен в г. транзит')
    TAKEN_BY_TRANSPORTER_FROM_SENDER_CITY = 'TAKEN_BY_TRANSPORTER_FROM_SENDER_CITY', __('Выдан на доставку')
    TAKEN_BY_TRANSPORTER_FROM_TRANSIT_CITY = 'TAKEN_BY_TRANSPORTER_FROM_TRANSIT_CITY', __('Сдан перевозчику в г. отправителе')
    # В банке
    DELIVERED = 'DELIVERED', __('Вручен')
    # Регистрация откаха
    NOT_DELIVERED = 'NOT_DELIVERED', __('Некорректный заказ')
