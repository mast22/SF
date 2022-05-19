# TODO лучше расширить кол-во возможных вариантов для всех банков
#  В МТС для частной и международной отправляется "не знаю"
from apps.banks.const import BankBrand

ORG_OWNERSHIP = [
    {
        'general': 'STATE',
        'desc': 'Государственная компания',
        'specific': {BankBrand.OTP: 'Государственная компания/учреж', BankBrand.ALFA: 'STATE',
                     BankBrand.MTS: 'WORK.FORM.5'}
    },
    {
        'general': 'PRIVATE',
        'desc': 'Частная компания',
        'specific': {BankBrand.OTP: 'Частная компания', BankBrand.ALFA: 'PRIVATE', BankBrand.MTS: 'WORK.FORM.8' }
    },
    {
        'general': 'INTERNATIONAL',
        'desc': 'Международная',
        'specific': {BankBrand.OTP: 'Частная компания с иностранным', BankBrand.ALFA: 'INTER',
                     BankBrand.MTS: 'WORK.FORM.8'}
    },
]
