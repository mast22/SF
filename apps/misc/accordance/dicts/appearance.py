from apps.banks.const import BankBrand

APP_ACC = [
    {
        'desc': 'Хорошо',
        'general': 'SUCCESS',
        'specific': {BankBrand.OTP: ['У']}
    },
    {
        'desc': 'Подозрение на мошенничество',
        'general': 'FRAUD',
        'specific': {BankBrand.OTP: ['М']}
    },
    {
        'desc': 'Неадекватный',
        'general': 'INADEQUATE',
        'specific': {BankBrand.OTP: ['Н']}
    },
    {
        'desc': 'Подозрительный',
        'general': 'SUSPICIOUS',
        'specific': {BankBrand.OTP: ['В']}
    },
]
