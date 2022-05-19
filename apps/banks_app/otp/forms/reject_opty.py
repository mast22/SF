from django.conf import settings
from apps.orders.const import RejectReason
from ...base.forms import BaseBankForm


class RejectOptyBankForm(BaseBankForm):
    mapper = {
        'Environment_Code': {'converter': 'convert_calculated', 'callable': lambda _: settings.OTP_SW_CODE},
        'Opty_Id': {'converter': 'convert_transform', 'lookup': 'id', 'callable': lambda x: str(x)},
        'Archive_Reason': {'converter': 'convert_enum', 'lookup': 'reject_reason', 'mapper': {
            'REASON_01': RejectReason.NO_EXPLANATION,
            'REASON_02': RejectReason.INTEREST_RATE_TOO_HIGH,
            'REASON_03': RejectReason.INSUFFICIENT_LIMIT,
            'REASON_04': RejectReason.LENGTHY_SCORING,
            'REASON_05': RejectReason.OTHER,
            'REASON_06': RejectReason.POOR_SERVICE,
            'REASON_07': RejectReason.OTHER_BANK,
            'REASON_08': RejectReason.AUTH_DID_NOT_COMPLETE,
            'REASON_09': RejectReason.PAYMENT_TOO_HIGH,
            'REASON_10': RejectReason.EARLY_REPAYMENT_COMMISSION_TOO_HIGH,
            'REASON_11': RejectReason.LOAN_COMMISSION_TOO_HIGH,
            'REASON_12': RejectReason.LOAN_NO_MORE_NEEDED,
            'REASON_13': RejectReason.TECH_FAILURE,
            'REASON_14': RejectReason.BANK_REJECTION,
        }, 'default': 'REASON_01'}
    }
