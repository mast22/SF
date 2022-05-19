"""
Типы должностей банков

В документации ОТП выделено синим цветом 4 типа, видимо только их обрабатывают, несмотря
на наличие ещё пары других. Почта предлагает 5 вариантов, включая "военнослужащего"
Для облегчения поддержки системы я его исключу их вариантов и добавлю только 4 типы,
аналогичных другим банкам.
"""
from apps.banks.const import BankBrand

POSITION_TYPE = [
    {
        'general': 'SPEC',
        'desc': 'Специалист',
        'specific': {BankBrand.OTP: 'Специалист', BankBrand.ALFA: 'SPECIALIST', BankBrand.POCHTA: 'Employee' }
    },
    {
        'general': 'MANAGER',
        'desc': 'Руководитель низшего звена',
        'specific': {BankBrand.OTP: 'Руководитель низшего звена', BankBrand.ALFA: 'MANAGER',
                     BankBrand.POCHTA: 'Middle management'}
    },
    {
        'general': 'TOP_MANAGER',
        'desc': 'Руководитель высшего звена',
        'specific': {BankBrand.OTP: 'Руководитель высшего звена', BankBrand.ALFA: 'TOP_MANAGER',
                     BankBrand.POCHTA: 'Senior Manager'}
    },
    {
        'general': 'OWNER',
        'desc': 'Предприниматель/владелец бизнеса',
        'specific': {BankBrand.OTP: 'Индивидуальный предприниматель', BankBrand.ALFA: 'SELF_EMPL',
                     BankBrand.POCHTA: 'Administrative staff'}
    },
]
