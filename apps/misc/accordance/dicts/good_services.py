from apps.banks.const import BankBrand

GOOD_SERVICES = [
    {
        'general': 'CLOTHING_INSURANCE',
        'desc': 'Защита покупки (одежда)',
        'specific': {BankBrand.OTP: 'Outer clothing Insurance'}
    },
    {
        'general': 'PROPERTY_INSURANCE',
        'desc': 'Защита покупки',
        'specific': {BankBrand.OTP: 'Property Insurance'}
    },
]
