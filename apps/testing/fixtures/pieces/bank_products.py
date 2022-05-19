from django.conf import settings
from typing import Mapping, Sequence, Tuple
from decimal import Decimal
from apps.banks import models as m
from apps.partners.models import PartnerBank, Outlet, OutletAgent
from apps.banks.const import BankBrand
from dataclasses import dataclass
from django.core.files.base import File
import os

from apps.users.models import Agent


@dataclass
class BankWithOffer:
    bank: m.Bank
    extra_service: m.ExtraService
    credit_product: m.CreditProduct


def create_bank(bank_name):
    bank = m.Bank.objects.create(name=bank_name)
    bank_name_l = bank_name.lower()
    logos_dir = os.path.join(settings.BASE_DIR, 'apps', 'testing', 'fixtures', 'static', 'bank_logos')
    with open(os.path.join(logos_dir, f'{bank_name_l}-logo.svg')) as f:
        bank.logo.save(f'{bank_name_l}_logo.svg', File(f))
    return bank


def create_banks() -> Tuple[m.Bank, ...]:
    otp_bank = create_bank(BankBrand.OTP)
    alfa_bank = create_bank(BankBrand.ALFA)
    pochta_bank = create_bank(BankBrand.POCHTA)
    mts_bank = create_bank(BankBrand.MTS)

    return otp_bank, alfa_bank, pochta_bank, mts_bank


def create_credit_product(bank: m.Bank, code: str = None, save=True) -> m.CreditProduct:
    credit_product = m.CreditProduct(
        bank=bank,
        name=f'Самый выгодный в банке {bank.name}',
        annual_rate=24,
        total_min=1000,
        total_max=50000,
        term_min=3,
        term_max=24,
        initial_payment_min=500,
        initial_payment_max=30000,
        code=code,
    )
    if save:
        credit_product.save()

    return credit_product


def create_extra_service(bank: m.Bank, save=True) -> m.ExtraService:
    extra_service = m.ExtraService(
        bank=bank,
        name='Life Insurance',
        price=100.10,
    )
    if save:
        extra_service.save()

    return extra_service


def create_bank_structure(credit_product_codes: dict=None) -> Tuple[BankWithOffer, ...]:
    otp_bank, alfa_bank, pochta_bank, mts_bank = create_banks()

    cp_code = credit_product_codes.get(BankBrand.OTP, None) if credit_product_codes else None
    credit_product = create_credit_product(otp_bank, code=cp_code)
    extra_service = create_extra_service(otp_bank)
    otp_with_offers = BankWithOffer(otp_bank, extra_service, credit_product)

    cp_code = credit_product_codes.get(BankBrand.ALFA, None) if credit_product_codes else None
    credit_product = create_credit_product(alfa_bank, cp_code)
    extra_service = create_extra_service(alfa_bank)
    alfa_with_offers = BankWithOffer(alfa_bank, extra_service, credit_product)

    cp_code = credit_product_codes.get(BankBrand.ALFA, None) if credit_product_codes else None
    credit_product = create_credit_product(pochta_bank, cp_code)
    extra_service = create_extra_service(pochta_bank)
    pochta_with_offers = BankWithOffer(pochta_bank, extra_service, credit_product)

    cp_code = credit_product_codes.get(BankBrand.MTS, None) if credit_product_codes else None
    credit_product = create_credit_product(mts_bank, cp_code)
    extra_service = create_extra_service(mts_bank)
    mts_with_offers = BankWithOffer(mts_bank, extra_service, credit_product)

    return otp_with_offers, alfa_with_offers, pochta_with_offers, mts_with_offers


def set_agent_commissions(agent, ter_man, bank: m.Bank, credit_product: m.CreditProduct,
        extra_service: m.ExtraService, agent_code=None):
    """Создаёт связки территориала и агента с банком, кредитным продуктом и доп. услугой."""
    tb = m.TerManBank.objects.create(ter_man=ter_man, bank=bank, is_active=True, priority=1)
    tcp = m.TerManCreditProduct.objects.create(terman_bank=tb, credit_product=credit_product,
            commission_min=Decimal(0.25), commission_max=Decimal(2.28), is_active=True)
    tes = m.TerManExtraService.objects.create(terman_bank=tb, extra_service=extra_service,
            commission_min=Decimal(0.11), commission_max=Decimal(15.31), is_active=True)

    # Назначим коммиссию агента на кредитный продукт и дополнительную услугу
    ab = m.AgentBank.objects.create(agent=agent, bank=bank, terman_bank=tb, is_active=True, code=agent_code)
    acp = m.AgentCreditProduct.objects.create(credit_product=credit_product, agent_bank=ab,
            commission=Decimal(1.5), is_active=True, terman_credit_product=tcp)
    aes = m.AgentExtraService.objects.create(extra_service=extra_service, agent_bank=ab,
        commission=Decimal(1.5), is_active=True, terman_extra_service=tes)
    return tb, tcp, tes, ab, acp, aes


def set_outlet_banks(outlet, banks: Sequence[m.Bank], outlet_codes: Mapping[str, str]=None):
    """Назначает все кредитный продукты и доп. услуги банка на заданную торговую точку."""
    outlet_banks = []
    for bank in banks:
        outlet_code = outlet_codes.get(bank.name, None) if outlet_codes else None
        outlet_bank = m.OutletBank.objects.create(outlet=outlet, bank=bank,
            is_active=True, code=outlet_code)

        cps = m.CreditProduct.objects.filter(bank=bank, is_active=True)
        outlet_credit_products = [
            m.OutletCreditProduct(credit_product=cp, outlet_bank=outlet_bank, is_active=True)
            for cp in cps
        ]
        m.OutletCreditProduct.objects.bulk_create(outlet_credit_products)

        ess = m.ExtraService.objects.filter(bank=bank, is_active=True)
        outlet_extra_services = [
            m.OutletExtraService(extra_service=es, outlet_bank=outlet_bank, is_active=True)
            for es in ess
        ]
        m.OutletExtraService.objects.bulk_create(outlet_extra_services)
        outlet_banks.append(outlet_bank)
    return outlet_banks


def set_partner_banks(partner, banks: Sequence[m.Bank], partner_codes: Mapping[str, str]=None):
    partner_banks = []
    for bank in banks:
        partner_code = partner_codes.get(bank.name)
        partner_bank = PartnerBank(partner=partner, bank=bank, code=partner_code)
        partner_banks.append(partner_bank)
    PartnerBank.objects.bulk_create(partner_banks)
    return partner_banks


def set_outlet_agents(outlet: Outlet, agent: Agent):
    OutletAgent.objects.create(agent=agent, outlet=outlet)
