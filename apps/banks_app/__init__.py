"""
Приложение для взаимодействия с api банков. Минимально привязано к Django.
"""
import logging
logger = logging.getLogger('banks')

from .otp.provider import OTPBankProvider
from .alpha.provider import AlphaBankProvider
from .pochta.provider import PochtaBankProvider
from .mts.provider import MTSBankProvider
