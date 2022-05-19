from apps.common.choices import Choices
from django.utils.translation import gettext_lazy as __


class AccordanceCollection(Choices):
    INDUSTRY = 'industry', __('Индустрия организации клиента банка')
    APPEARANCE = 'appearance', __('Внешний вид клиента')
    GOOD_CATEGORY = 'good_category', __('Категория товара')
    GOOD_SERVICES = 'good_service', __('Программы услуг для товара')
    POSITION_TYPE = 'position_type', __('Тип должности клиента')
    ORG_OWNERSHIP = 'org_ownership', __('Форма собственности организации')


class AccordanceSpecifier(Choices):
    INDUSTRY_OTP = 'ind_otp', __('Индустрия организации банка ОТП')
    INDUSTRY_ALFA = 'ind_alfa', __('Индустрия организации АльфаБанка')

    APPEARANCE_OTP = 'app_otp', __('Внешний вид клиента для банка ОТП')
    APPEARANCE_ALFA = 'app_alfa', __('Внешний вид клиента для АльфаБанка')

    GOOD_CATEGORY_OTP = 'gc_otp', __('Категория товаров для банка ОТП')
    GOOD_CATEGORY_ALFA = 'gc_alfa', __('Категория товаров для АльфаБанка')
    GOOD_CATEGORY_POCHTA = 'gc_pochta', __('Категория товаров для Почта банка')

    GOOD_SERVICES_OTP = 'gs_otp', __('Программа услуг товара для банка ОТП')
    GOOD_SERVICES_ALFA = 'gs_alfa', __('Программа услуг товара для АльфаБанка')

    POSITION_TYPE_OTP = 'position_type_otp', __('Тип должности для банка ОТП')
    POSITION_TYPE_ALFA = 'position_type_alfa', __('Тип должности для АльфаБанка')
    POSITION_TYPE_POCHTA = 'position_type_pochta', __('Тип должности для Почта Банк')

    ORG_OWNERSHIP_OTP = 'org_ownership_otp', __('Форма собственности организации для банка ОТП')
    ORG_OWNERSHIP_ALFA = 'org_ownership_alfa', __('Форма собственности организации для АльфаБанка')
    ORG_OWNERSHIP_MTS = 'org_ownership_mts', __('Форма собственности организации для МТС')
