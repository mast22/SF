from .order import OrderViewSet, OrderHistoryViewSet, TelegramOrderViewSet, XLSXOrderList
from .order_credits import OrderCreditProductViewSet, OrderExtraServiceViewSet
from .order_flow import (
    GoodViewSet,
    OrderGoodViewSet,
    OrderGoodServicesViewSet,
    CreditViewSet,
    PassportViewSet,
    PersonalDataViewSet,
    FamilyDataViewSet,
    CareerEducationViewSet,
    ExtraDataViewSet,
)
from .client import ClientsViewSet, ClientOrderViewSet
from .documents import ContractViewSet, DocumentsSignedViewSet, DocumentsToSignViewSet
