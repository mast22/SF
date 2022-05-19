from django.urls import path, include
from django.conf import settings

from apps.common.routers import DefaultRouter, NestedRouter
from apps.users.api import views as users_views
from apps.users.auth import urls as auth_urls
from apps.banks.api import views as banks_views
from apps.banks import urls as soap_urls
from apps.deliveries.api import views as contract_views
from apps.orders.api import views as orders_views
from apps.partners.api import views as partners_views
from apps.misc.api import views as misc_views
from .schema import urlpatterns as schema_urlpatterns
from .apps import ApiConfig

router = DefaultRouter()
# users
router.register_resource(users_views.UserViewSet)
router.register_resource(users_views.AllowedIpsViewSet)
router.register_resource(users_views.AccManViewSet)
router.register_resource(users_views.TerManViewSet)
router.register_resource(users_views.AgentViewSet)
router.register_resource(users_views.AdminViewSet)

# partners
router.register_resource(partners_views.RegionViewSet)
router.register_resource(partners_views.PartnerViewSet)
router.register_resource(partners_views.OutletViewSet)
router.register_resource(partners_views.OutletAgentViewSet)
router.register_resource(partners_views.LocationViewSet)
router.register_resource(partners_views.PartnerBankViewSet)

# orders
router.register_resource(orders_views.ClientsViewSet)
router.register_resource(orders_views.OrderViewSet)
router.register_resource(orders_views.CreditViewSet)
router.register_resource(orders_views.PassportViewSet)
router.register_resource(orders_views.PersonalDataViewSet)
router.register_resource(orders_views.FamilyDataViewSet)
router.register_resource(orders_views.CareerEducationViewSet)
router.register_resource(orders_views.ExtraDataViewSet)
router.register_resource(orders_views.TelegramOrderViewSet)
router.register_resource(orders_views.GoodViewSet)
router.register_resource(orders_views.OrderGoodViewSet)
router.register_resource(orders_views.OrderGoodServicesViewSet)
router.register_resource(orders_views.ClientOrderViewSet)
router.register_resource(orders_views.OrderHistoryViewSet)
router.register_resource(orders_views.ContractViewSet)
router.register_resource(orders_views.OrderCreditProductViewSet)
router.register_resource(orders_views.OrderExtraServiceViewSet)
router.register_resource(orders_views.DocumentsToSignViewSet)
router.register_resource(orders_views.DocumentsSignedViewSet)

# banks
router.register_resource(banks_views.BankViewSet)
# router.register_resource(banks_views.BankPriorityViewSet)
router.register_resource(banks_views.CreditProductViewSet)
router.register_resource(banks_views.ExtraServiceViewSet)
router.register_resource(banks_views.AgentBankViewSet)
router.register_resource(banks_views.AgentCreditProductViewSet)
router.register_resource(banks_views.AgentExtraServicesViewSet)
router.register_resource(banks_views.OutletBankViewSet)
router.register_resource(banks_views.OutletCreditProductsViewSet)
router.register_resource(banks_views.OutletExtraServicesViewSet)
router.register_resource(banks_views.TerManBankViewSet)
router.register_resource(banks_views.TerManCreditProductViewSet)
router.register_resource(banks_views.TerManExtraServiceViewSet)
router.register_resource(banks_views.CreditProductsCalculateViewSet, basename='credit-products-calculate')
# router.register_resource(banks_views.AgentOutletCreditProductViewSet)
# router.register_resource(banks_views.AgentOutletExtraServiceViewSet)


# contract
router.register_resource(contract_views.DeliveryViewSet)

# misc
router.register_resource(misc_views.AccordanceViewSet)
router.register_resource(misc_views.MesaBankViewSet)

# Nested Routes:
order_router = NestedRouter(router, 'orders', lookup='order')
order_router.register_resource(banks_views.OrderChoosableCreditProductsViewSet, basename='order-credit-products')
order_router.register_resource(banks_views.OrderChoosableExtraServicesViewSet, basename='order-extra-services')


if settings.DEBUG:
    from apps.testing.api import DummyMessageViewSet
    router.register_resource(DummyMessageViewSet)


app_name = ApiConfig.name
urlpatterns = [
    path('', include(router.urls)),
    path('', include(order_router.urls)),
    path('orders-xlsx/', orders_views.XLSXOrderList.as_view(), name='orders-xlsx'),
    path('auth/', include(auth_urls, namespace='auth')),
    path('soap/', include(soap_urls, namespace='soap')),
] + schema_urlpatterns
